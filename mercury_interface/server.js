const express = require('express');
const OpenAI = require('openai');
const multer = require('multer');
const path = require('path');
const fs = require('fs');
const { spawn, spawnSync, exec } = require('child_process');
const app = express();
const port = process.env.PORT || 5000;

// Define openaiConfig and modelToUse variables
let openaiConfig = {
  apiKey: process.env.OPENAI_API_KEY,
};
let modelToUse = 'gpt-3.5-turbo'; // Default model

// Set up middleware
app.use(express.json());
app.use(express.static(path.join(__dirname, 'public')));

// Verify environment variables are set
if (!process.env.NVIDIA_API_KEY) {
  console.warn('Warning: NVIDIA_API_KEY environment variable is not set');
}

if (!process.env.OPENAI_API_KEY) {
  console.warn('Warning: OPENAI_API_KEY environment variable is not set');
}

// Global variable to store the recording process
let recordProcess = null;
const outputFilePath = '/tmp/mercury_recording.wav'; // Using /tmp directory for temporary audio file

/**
 * Parse image metadata from Mercury Agent response
 * Detects if response contains generated image information
 * @param {string} response - The agent's response text
 * @returns {object} - Object containing image info or null
 */
function parseImageMetadata(response) {
  try {
    // Check if response contains image metadata (location marker)
    const imagePathMatch = response.match(/📁 Location:\s*(.+\.jpg)/);
    
    if (imagePathMatch) {
      const fullPath = imagePathMatch[1].trim();
      const filename = path.basename(fullPath);
      
      // Extract other metadata if present
      const promptMatch = response.match(/📝 Prompt:\s*(.+)/);
      const seedMatch = response.match(/🎲 Seed:\s*(\d+)/);
      const sizeMatch = response.match(/📏 Size:\s*(\d+x\d+)/);
      const timeMatch = response.match(/⏱️ Generation time:\s*([\d.]+)s/);
      
      const imageInfo = {
        hasImage: true,
        filename: filename,
        fullPath: fullPath,
        url: `/api/images/${filename}`,
        prompt: promptMatch ? promptMatch[1].trim() : null,
        seed: seedMatch ? seedMatch[1] : null,
        size: sizeMatch ? sizeMatch[1] : null,
        generationTime: timeMatch ? timeMatch[1] : null
      };
      
      console.log('Detected image metadata:', imageInfo);
      return imageInfo;
    }
    
    return { hasImage: false };
  } catch (error) {
    console.error('Error parsing image metadata:', error);
    return { hasImage: false };
  }
}

// Configure multer for file uploads
const storage = multer.diskStorage({
  destination: function (req, file, cb) {
    cb(null, 'uploads/');
  },
  filename: function (req, file, cb) {
    cb(null, Date.now() + path.extname(file.originalname));
  }
});

const upload = multer({ storage: storage });

// Root route to serve the HTML file
app.get('/', (req, res) => {
  res.sendFile(path.join(__dirname, 'public', 'index.html'));
});

// API endpoint to serve generated images
app.get('/api/images/:filename', (req, res) => {
  try {
    const filename = req.params.filename;
    // Sanitize filename to prevent directory traversal
    const safeFilename = path.basename(filename);
    const imagePath = path.join('/tmp/mercury_images', safeFilename);
    
    console.log(`Image request for: ${safeFilename}`);
    
    if (fs.existsSync(imagePath)) {
      console.log(`Serving image: ${imagePath}`);
      res.sendFile(imagePath);
    } else {
      console.error(`Image not found: ${imagePath}`);
      res.status(404).json({ error: 'Image not found' });
    }
  } catch (error) {
    console.error('Error serving image:', error);
    res.status(500).json({ error: 'Failed to serve image' });
  }
});

// API endpoint to handle browser-uploaded audio for transcription
app.post('/api/transcribe-audio', upload.single('audio'), async (req, res) => {
  try {
    if (!req.file) {
      return res.status(400).json({ error: 'No audio file uploaded' });
    }
    
    console.log('Received audio file:', req.file.originalname, req.file.size, 'bytes');
    
    const inputFile = req.file.path;
    const outputWavFile = `/tmp/converted_${Date.now()}.wav`;
    
    // Convert WebM/audio to WAV format (16kHz, mono, 16-bit) using ffmpeg
    const convertProcess = spawnSync('ffmpeg', [
      '-i', inputFile,
      '-ar', '16000',  // 16kHz sample rate
      '-ac', '1',      // Mono channel
      '-sample_fmt', 's16',  // 16-bit signed
      '-y',            // Overwrite output file
      outputWavFile
    ]);
    
    if (convertProcess.error || convertProcess.status !== 0) {
      console.error('FFmpeg conversion error:', convertProcess.stderr.toString());
      fs.unlinkSync(inputFile);
      return res.status(500).json({ error: 'Failed to convert audio format' });
    }
    
    console.log('Audio converted to WAV format');
    console.log('Starting transcription...');
    
    // Transcribe the converted audio using Parakeet 0.6B ASR (offline mode)
    const transcribeProcess = spawn('python', [
      '/home/milos/mercury-assistant/mercury_interface/riva_python_client/scripts/asr/transcribe_file_offline.py',
      '--server', 'localhost:50051',
      '--input-file', outputWavFile
    ]);
    
    let transcriptionData = '';
    let errorData = '';
    
    transcribeProcess.stdout.on('data', (data) => {
      transcriptionData += data.toString();
    });
    
    transcribeProcess.stderr.on('data', (data) => {
      errorData += data.toString();
      console.error(`Transcription stderr: ${data}`);
    });
    
    transcribeProcess.on('close', (code) => {
      console.log(`Transcription process exited with code: ${code}`);
      console.log(`Transcription output: "${transcriptionData}"`);
      
      // Clean up temp files
      try {
        fs.unlinkSync(inputFile);
        fs.unlinkSync(outputWavFile);
      } catch (err) {
        console.error('Error deleting temp files:', err);
      }
      
      if (code !== 0) {
        console.error(`Transcription failed with error: ${errorData}`);
        return res.status(500).json({
          error: 'Transcription failed',
          details: errorData
        });
      }
      
      // Process transcription output - extract "Final transcript:" line from offline script
      let transcription = '';
      const lines = transcriptionData.trim().split('\n');
      for (const line of lines) {
        if (line.startsWith('Final transcript:')) {
          transcription = line.replace('Final transcript:', '').trim();
          break;
        }
      }
      
      if (!transcription || transcription.length === 0) {
        console.warn('Empty transcription received');
        return res.status(500).json({ 
          error: 'No speech detected. Please speak clearly and try again.'
        });
      }
      
      res.json({ success: true, transcription });
    });
    
  } catch (error) {
    console.error('Error processing audio:', error);
    res.status(500).json({ error: 'Failed to process audio: ' + error.message });
  }
});

// API endpoint to stop recording and transcribe
app.post('/api/stop-recording', (req, res) => {
  try {
    // Stop the recording process
    if (recordProcess) {
      // Send SIGINT (Ctrl+C) instead of SIGTERM for cleaner shutdown
      recordProcess.kill('SIGINT');
      recordProcess = null;
      console.log('Recording stopped');
    }
    
    // Wait for the file to be properly saved (increased to 2 seconds)
    setTimeout(() => {
      // Check if the file exists
      if (!fs.existsSync(outputFilePath)) {
        console.error('Recording file not found at:', outputFilePath);
        return res.status(500).json({ error: 'Recording file not found' });
      }
      
      console.log('Starting transcription for file:', outputFilePath);
      
      // Run the transcription script with the correct absolute path
      // Using Parakeet 0.6B ASR on port 9000/50051 (offline mode)
      const transcribeProcess = spawn('python', [
        '/home/milos/mercury-assistant/mercury_interface/riva_python_client/scripts/asr/transcribe_file_offline.py',
        '--server', 'localhost:50051',  // Local Parakeet 0.6B ASR server
        '--input-file', outputFilePath
      ]);
      
      let transcriptionData = '';
      let errorData = '';
      
      transcribeProcess.stdout.on('data', (data) => {
        transcriptionData += data.toString();
      });
      
      transcribeProcess.stderr.on('data', (data) => {
        errorData += data.toString();
        console.error(`Transcription stderr: ${data}`);
      });
      
      transcribeProcess.on('close', (code) => {
        console.log(`Transcription process exited with code: ${code}`);
        console.log(`Transcription stdout data length: ${transcriptionData.length}`);
        console.log(`Transcription stdout data: "${transcriptionData}"`);
        console.log(`Transcription stderr data length: ${errorData.length}`);
        
        if (code !== 0) {
          console.error(`Transcription process exited with code ${code}`);
          console.error(`Stderr: ${errorData}`);
          return res.status(500).json({
            error: 'Transcription failed',
            details: errorData
          });
        }
        
        // Extract the transcription text from the offline script output
        let transcription = '';
        const lines = transcriptionData.trim().split('\n');
        for (const line of lines) {
          if (line.startsWith('Final transcript:')) {
            transcription = line.replace('Final transcript:', '').trim();
            break;
          }
        }
        
        console.log(`Final transcription after processing: "${transcription}"`);
        
        // Don't delete file for debugging - copy it first
        const debugFilePath = `/tmp/mercury_recording_${Date.now()}.wav`;
        try {
          fs.copyFileSync(outputFilePath, debugFilePath);
          console.log(`Debug: Audio file saved to ${debugFilePath}`);
        } catch (err) {
          console.error('Error copying debug file:', err);
        }
        
        if (!transcription || transcription.length === 0) {
          console.warn('Empty transcription received');
          console.warn(`Audio file size: ${fs.statSync(outputFilePath).size} bytes`);
          return res.status(500).json({ 
            error: 'No transcription received. Audio may be too quiet or microphone not working.'
          });
        }

        // Clean up the output file
        try {
          fs.unlinkSync(outputFilePath);
        } catch (err) {
          console.error('Error deleting recording file:', err);
        }
        
        res.json({ success: true, transcription });
      });
    }, 2000); // Wait 2 seconds for the file to be properly saved
  } catch (error) {
    console.error('Error stopping recording or transcribing:', error);
    res.status(500).json({ error: 'Failed to process recording' });
  }
});

// Regular API endpoint for non-streaming responses
app.post('/api/chat', async (req, res) => {
  console.log('Received request to /api/chat');
  const { model, message } = req.body;
  console.log(`Model: ${model}, Message: ${message}`);
  
  // Default to mercury-agent if no model specified
  const modelToCheck = model || 'mercury-agent';
  console.log(`Using model: ${modelToCheck}`);
  
  try {
    // NVIDIA-specific configuration
    if (modelToCheck.includes('llama-3.1-405b') || modelToCheck.includes('meta/')) {
      if (!process.env.NVIDIA_API_KEY) {
        return res.status(500).json({ error: 'NVIDIA API key not configured' });
      }
      openaiConfig = {
        apiKey: process.env.NVIDIA_API_KEY,
        baseURL: 'https://integrate.api.nvidia.com/v1',
      };
      modelToUse = 'nvdev/meta/llama-3.1-405b-instruct';
    }
    // NIM LLM configuration
    else if (modelToCheck.includes('nemotron')) {
      if (!process.env.NVIDIA_API_KEY) {
        return res.status(500).json({ error: 'NVIDIA API key not configured' });
      }
      openaiConfig = {
        apiKey: process.env.NVIDIA_API_KEY,
        baseURL: 'https://integrate.api.nvidia.com/v1',
      };
      modelToUse = 'nvdev/nvidia/llama-3.3-nemotron-super-49b-v1';
    }
    // NIM LLM configuration
    else if (modelToCheck === 'nim-llm') {
      openaiConfig = {
        apiKey: 'not-required',
        baseURL: 'http://0.0.0.0:8000',
      };
      modelToUse = 'meta/llama-3.1-8b-instruct';
    }
    // OpenAI configuration
    else if (modelToCheck.includes('gpt')) {
      if (!process.env.OPENAI_API_KEY) {
        return res.status(500).json({ error: 'OpenAI API key not configured' });
      }
      openaiConfig = {
        apiKey: process.env.OPENAI_API_KEY,
      };
      modelToUse = modelToCheck;
    }
    // Claude configuration
    else if (modelToCheck.includes('claude')) {
      // This would need Anthropic's API client instead
      return res.status(501).json({ error: 'Claude API not yet implemented' });
    }
    // Custom endpoint
    else if (modelToCheck === 'custom') {
      // Would need to get custom endpoint details from request
      return res.status(501).json({ error: 'Custom endpoint not yet implemented' });
    }
    // Mercury Agent configuration
    else if (modelToCheck === 'mercury-agent') {
      if (!process.env.NVIDIA_API_KEY) {
        return res.status(500).json({ error: 'NVIDIA API key not configured' });
      }
      
      console.log('Starting Mercury Agent process...');
      // Execute Mercury Agent process
      const mercuryProcess = spawn('nat', [
        'run',
        '--config_file=/home/milos/mercury-assistant/mercury_agent/configs/config.yml',
        '--input',
        message
      ]);

      let output = '';
      let error = '';

      mercuryProcess.stdout.on('data', (data) => {
        const chunk = data.toString();
        console.log('Mercury Agent stdout chunk:', chunk);
        output += chunk;
      });

      mercuryProcess.stderr.on('data', (data) => {
        const chunk = data.toString();
        console.log('Mercury Agent stderr chunk:', chunk);
        error += chunk;
      });

      mercuryProcess.on('close', (code) => {
        console.log('Mercury Agent process closed with code:', code);
        console.log('Full output:', output);
        console.log('Full error:', error);

        if (code !== 0) {
          console.error('Mercury Agent process exited with code:', code);
          console.error('Error:', error);
          return res.status(500).json({ error: 'Mercury Agent process failed' });
        }

        // Combine stdout and stderr for processing
        // Note: Mercury Agent can output responses in either stream
        const combinedOutput = output + error;

        // Clean the output by removing ANSI color codes and other control characters
        // This ensures consistent parsing regardless of terminal formatting
        const cleanOutput = combinedOutput
          .replace(/\x1B\[[0-9;]*[a-zA-Z]/g, '') // Remove ANSI color codes
          .replace(/\x1B\]0;/g, '')              // Remove other ANSI escape sequences
          .replace(/\r/g, '')                    // Remove carriage returns
          .trim();

        console.log('Cleaned output:', cleanOutput);

        // Parse Mercury Agent responses
        // The agent can return responses in two formats:
        // 1. Standard format: Workflow Result: ["content"] or Workflow Result: ['content']
        // 2. Research tool format: Workflow Result: ['<Document>content</Document>']
        
        // First try to find the standard Workflow Result format
        // The pattern matches both single and double quotes: ['content'] or ["content"]
        // Also handles escaped quotes within the content
        const workflowResultMatch = cleanOutput.match(/Workflow Result:\s*\[['"](.*?)['"]\]/s);
        if (workflowResultMatch && workflowResultMatch[1]) {
          const cleanContent = workflowResultMatch[1]
            .replace(/\\n/g, '\n')  // Replace escaped newlines with actual newlines
            .replace(/\\'/g, "'")   // Replace escaped single quotes
            .replace(/\\"/g, '"')   // Replace escaped double quotes
            .trim();                // Remove extra whitespace
          
          console.log('Extracted content:', cleanContent);
          
          // Check if response contains image metadata
          const imageInfo = parseImageMetadata(cleanContent);
          
          if (imageInfo.hasImage) {
            console.log('Response contains image, including metadata in response');
            return res.json({ 
              text: cleanContent,
              image: imageInfo
            });
          }
          
          return res.json({ text: cleanContent });
        }

        // If that fails, try to find the Research tool's document format
        // This format includes XML-like document tags and is used for Wikipedia research
        const researchResultMatch = cleanOutput.match(/Workflow Result:\s*\['<Document[^>]*>\\n(.*?)\\n<\/Document>'\]/s);
        if (researchResultMatch && researchResultMatch[1]) {
          const cleanContent = researchResultMatch[1]
            .replace(/\\n/g, '\n')  // Replace escaped newlines with actual newlines
            .replace(/\\'/g, "'")   // Replace escaped single quotes
            .replace(/\\"/g, '"')   // Replace escaped double quotes
            .trim();                // Remove extra whitespace
          
          console.log('Extracted content from Research tool:', cleanContent);
          return res.json({ text: cleanContent });
        }

        // If we couldn't find either format, return an error
        console.error('Could not find Workflow Result with expected format');
        return res.status(500).json({ error: 'Could not parse Mercury Agent response' });
      });
      return; // Important: return here to prevent further execution
    }
    
    // Configure OpenAI client after setting the configuration
    const openai = new OpenAI(openaiConfig);
    console.log(`Using model: ${modelToUse} with baseURL: ${openaiConfig.baseURL || 'default OpenAI URL'}`);
    
    // NIM LLM configuration
    if (model === 'nim-llm') {
      try {
        console.log('Using direct fetch for NIM LLM');
        const response = await fetch('http://0.0.0.0:8000/v1/chat/completions', {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
            'Accept': 'application/json'
          },
          body: JSON.stringify({
            model: 'meta/llama-3.1-8b-instruct',
            messages: [{"role": "user", "content": message}],
            max_tokens: 8192,
            temperature: 0.2
          })
        });
        
        if (!response.ok) {
          const errorText = await response.text();
          console.error(`Error status: ${response.status}`);
          console.error(`Error response: ${errorText}`);
          return res.status(500).json({
            error: `NIM API error: ${response.status} - ${errorText}`
          });
        }
        
        const data = await response.json();
        console.log('Direct fetch response received');
        return res.json({ text: data.choices[0].message.content });
      } catch (error) {
        console.error('Direct fetch error:', error);
        return res.status(500).json({
          error: `Failed to get response from NIM: ${error.message}`
        });
      }
    }
    
    // Adjust parameters based on model
    let systemMessage = {
      "role": "system", 
      "content": "Format your response using markdown. Use ### for main headers, ** for bold text, and proper list formatting with - for bullet points and 1. for numbered lists. Ensure nested lists are properly indented."
    };

    if (modelToCheck.includes('nemotron')) {
      let completionParams = {
        model: modelToUse,
        messages: [{"role":"system","content":"Give me thoughtful and rational input about the following subject:"}, {"role": "user", "content": message}],
        temperature: 0.6,
        top_p: 0.95,
        max_tokens: 8092,
        frequency_penalty: 0,
        presence_penalty: 0,
        stream: false
      };
      try {
        const completion = await openai.chat.completions.create(completionParams);
        console.log("Received response from Nemotron API");
        return res.json({ text: completion.choices[0].message.content });
      } catch (error) {
        console.error('Error calling Nemotron API:', error);
        return res.status(500).json({ error: `Failed to get response from Nemotron model: ${error.message}` });
      }
    } else {
      completionParams = {
        model: modelToUse,
        messages: [{"role": "user", "content": message}],
        temperature: 0.2,
        top_p: 0.7,
        max_tokens: 8192,
        stream: false
      };
      const completion = await openai.chat.completions.create(completionParams);
      console.log("Received response from API");
      res.json({ text: completion.choices[0].message.content });
    }

  } catch (error) {
    console.error('Error calling AI API:', error);
    res.status(500).json({ error: `Failed to get response from AI model: ${error.message}` });
  }
});

// Handle file uploads for RAG processing
app.post('/api/upload/document', upload.array('files'), (req, res) => {
  try {
    // Here you would process the uploaded files for RAG
    // This is a placeholder that just returns the file information
    const fileInfo = req.files.map(file => ({
      filename: file.filename,
      originalName: file.originalname,
      size: file.size,
      path: file.path
    }));
    res.json({ success: true, files: fileInfo });
  } catch (error) {
    console.error('Error handling file upload:', error);
    res.status(500).json({ error: 'Failed to process uploaded files' });
  }
});

// Handle image uploads for vision models
app.post('/api/upload/image', upload.array('images'), (req, res) => {
  try {
    // Here you would process the uploaded images for vision models
    // This is a placeholder that just returns the image information
    const imageInfo = req.files.map(file => ({
      filename: file.filename,
      originalName: file.originalname,
      size: file.size,
      path: file.path
    }));
    res.json({ success: true, images: imageInfo });
  } catch (error) {
    console.error('Error handling image upload:', error);
    res.status(500).json({ error: 'Failed to process uploaded images' });
  }
});

// Handle audio transcription
app.post('/api/transcribe', upload.single('audio'), async (req, res) => {
  try {
    // This is a placeholder - in a real implementation, you would:
    // 1. Process the audio file
    // 2. Send it to a speech-to-text service
    // 3. Return the transcription
    // For now, just return a mock response
    res.json({
      success: true,
      text: "This is a placeholder transcription. In a real implementation, this would be the transcribed text from your audio."
    });
  } catch (error) {
    console.error('Error transcribing audio:', error);
    res.status(500).json({ error: 'Failed to transcribe audio' });
  }
});

// TTS endpoint - Handles text-to-speech conversion using NVIDIA RIVA Magpie model
app.post('/api/tts', async (req, res) => {
    const { text, voice } = req.body;
    const timestamp = Date.now();
    const tempFiles = [];
    
    try {
        console.log('=== TTS Request Debug ===');
        console.log('Raw request body:', req.body);
        console.log('Text received:', text);
        console.log('Text length in characters:', text.length);
        console.log('Text length in words:', text.split(/\s+/).length);
        console.log('First 100 characters:', text.substring(0, 100));
        console.log('Last 100 characters:', text.substring(text.length - 100));
        console.log('=======================');
        
            // Split text into chunks of maximum 1000 characters to stay under gRPC 4MB message limit
            // (1474 chars generated 5MB, which exceeded the limit and caused silent failures)
            const MAX_CHUNK_SIZE = 1000;
        const textChunks = [];
        let currentChunk = '';
        
        // Split by sentences to maintain natural breaks
        const sentences = text.match(/[^.!?]+[.!?]+/g) || [text];
        
        for (const sentence of sentences) {
            if ((currentChunk + sentence).length <= MAX_CHUNK_SIZE) {
                currentChunk += sentence;
            } else {
                if (currentChunk) {
                    textChunks.push(currentChunk.trim());
                }
                currentChunk = sentence;
            }
        }
        if (currentChunk) {
            textChunks.push(currentChunk.trim());
        }
        
        console.log('=== TTS Chunking Debug ===');
        console.log(`Split text into ${textChunks.length} chunks`);
        textChunks.forEach((chunk, idx) => {
            console.log(`Chunk ${idx + 1}: ${chunk.length} chars - "${chunk.substring(0, 50)}..."`);
        });
        console.log('========================');
        
        // Process each chunk and combine the audio
        for (let i = 0; i < textChunks.length; i++) {
            const chunk = textChunks[i];
            console.log(`\n>>> Processing chunk ${i + 1}/${textChunks.length} (${chunk.length} characters)`);
            
            // Create a temporary file path for this chunk
            const tempFile = `/tmp/tts_${timestamp}_${i}.wav`;
            tempFiles.push(tempFile);
            console.log('Temporary file path:', tempFile);
            
            // Construct the path to the TTS script
            const scriptPath = path.join(__dirname, 'riva_python_client/scripts/tts/talk.py');
            
            // Spawn the TTS process for this chunk using Magpie TTS on port 50052
            const ttsProcess = spawn('python3', [
                scriptPath,
                '--server', 'localhost:50052',
                '--language-code', 'en-US',
                '--voice', voice || 'Magpie-Multilingual.EN-US.Jason.Happy',
                '--text', chunk,
                '-o', tempFile,
                '--encoding', 'LINEAR_PCM',
                '--sample-rate-hz', '22050'  // Updated to match source sample rate
            ]);

            let errorOutput = '';
            let stdoutOutput = '';

            // Capture and log standard output from the TTS process
            ttsProcess.stdout.on('data', (data) => {
                const output = data.toString();
                stdoutOutput += output;
                console.log('TTS stdout:', output);
            });

            // Capture and log any errors from the TTS process
            ttsProcess.stderr.on('data', (data) => {
                const error = data.toString();
                errorOutput += error;
                console.error('TTS stderr:', error);
            });

            // Wait for the TTS process to complete
            await new Promise((resolve, reject) => {
                ttsProcess.on('close', (code, signal) => {
                    console.log(`TTS process closed with code: ${code}, signal: ${signal}`);
                    if (code !== 0) {
                        console.error('TTS process failed with error output:', errorOutput);
                        reject(new Error(`TTS generation failed: ${errorOutput}`));
                    } else {
                        resolve();
                    }
                });

                ttsProcess.on('error', (error) => {
                    console.error('TTS process error:', error);
                    reject(error);
                });
            });

            // Verify the file was created and has content
            if (!fs.existsSync(tempFile)) {
              console.error(`❌ Chunk ${i + 1} FAILED: File not created`);
                throw new Error('TTS output file was not created');
            }
            const stats = fs.statSync(tempFile);
            if (stats.size === 0) {
                console.error(`❌ Chunk ${i + 1} FAILED: File is empty`);
                throw new Error('TTS output file is empty');
            }
            console.log(`✓ Chunk ${i + 1} SUCCESS: ${stats.size} bytes written to ${tempFile}`);
        }
        
        console.log('\n=== All chunks processed successfully ===');

        // Create a new WAV file with the combined audio
        const outputFile = `/tmp/tts_combined_${timestamp}.wav`;
        tempFiles.push(outputFile);
        
        console.log('\n=== Sox Combination ===');
        console.log('Files to combine:', tempFiles.slice(0, -1));
        console.log('Output file:', outputFile);
        console.log('Number of input files:', tempFiles.length - 1);
        
        // Use sox to combine the WAV files
        const soxArgs = [...tempFiles.slice(0, -1), outputFile];
        console.log('Sox command: sox', soxArgs.join(' '));
        const soxProcess = spawn('sox', soxArgs);
        
        let soxStderr = '';
        soxProcess.stderr.on('data', (data) => {
            soxStderr += data.toString();
            console.error('Sox stderr:', data.toString());
        });

        await new Promise((resolve, reject) => {
            soxProcess.on('close', (code) => {
                if (code === 0) {
                    console.log('✓ Sox combination successful');
                    resolve();
                } else {
                    console.error(`❌ Sox failed with code ${code}`);
                    console.error('Sox stderr output:', soxStderr);
                    reject(new Error(`Sox process failed with code ${code}: ${soxStderr}`));
                }
            });
        });

        // Verify the combined file exists and has content
        if (!fs.existsSync(outputFile)) {
            console.error('❌ Combined audio file was NOT created');
            throw new Error('Combined audio file was not created');
        }
        const stats = fs.statSync(outputFile);
        if (stats.size === 0) {
            console.error('❌ Combined audio file is EMPTY');
            throw new Error('Combined audio file is empty');
        }
        
        console.log(`✓ Combined audio file created: ${stats.size} bytes`);

        // Read the combined audio file
        const combinedAudio = fs.readFileSync(outputFile);
        console.log('✓ Combined audio loaded:', combinedAudio.length, 'bytes');
        console.log('=== TTS Generation Complete ===\n');
        
        // Set appropriate headers for audio streaming
        res.setHeader('Content-Type', 'audio/wav');
        res.setHeader('Content-Length', combinedAudio.length);
        
        // Send the combined audio data to the client
        res.send(combinedAudio);

    } catch (error) {
        console.error('Error in TTS endpoint:', error);
        if (!res.headersSent) {
            res.status(500).json({ 
                error: 'Internal server error',
                details: error.message
            });
        }
    } finally {
        // Clean up all temporary files
        // NOTE: Comment out this section to preserve files for debugging
        tempFiles.forEach(file => {
            try {
                if (fs.existsSync(file)) {
                    fs.unlinkSync(file);
                    console.log(`Cleaned up temporary file: ${file}`);
                }
            } catch (err) {
                console.error(`Error deleting temporary file ${file}:`, err);
            }
        });
    }
});

// Create uploads directory if it doesn't exist
if (!fs.existsSync('uploads')) {
  fs.mkdirSync('uploads');
}

// Start the server with error handling for port conflicts
function startServer(port) {
  app.listen(port, '0.0.0.0', () => {
    console.log(`Server running at http://0.0.0.0:${port}`);
    console.log(`Open your browser and navigate to http://192.168.4.67:${port}`);
  })
    .on('error', (err) => {
      if (err.code === 'EADDRINUSE') {
        console.log(`Port ${port} is busy, trying ${port + 1}...`);
        startServer(port + 1);
      } else {
        console.error('Server error:', err);
      }
    });
}

// Start the server
startServer(port);

