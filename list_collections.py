from pymilvus import connections, utility, Collection

# Connect to Milvus
connections.connect(
    alias="default",
    host="localhost",
    port="19530"
)

# Get the SPH collection
sph_collection = Collection("SPH")
sph_collection.load()

# Print collection info
print("\nSPH Collection Info:")
print("-------------------")
print(f"Description: {sph_collection.description}")
print(f"Schema: {sph_collection.schema}")
print(f"Number of entities: {sph_collection.num_entities}")

# Close connection
sph_collection.release()
connections.disconnect("default")
