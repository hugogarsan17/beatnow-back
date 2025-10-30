
from bson import ObjectId
from config.db import interactions_collection, post_collection
from routes.interactions_routes import count_likes, count_saved
# Change Stream to watch the interactions_collection
async def watch_changes():
    async with interactions_collection.watch() as stream:
        async for change in stream:
            if change["operationType"] == "insert":
                document = change["fullDocument"]
                post_id = document["post_id"]
                
                if "like_date" in document:
                    count= await count_likes(post_id)
                    await post_collection.update_one(
                        {"_id": ObjectId(post_id)},
                        {"$set": {"likes": count}}
                    )
                if "saved_date" in document:
                    count= await count_saved(post_id)
                    await post_collection.update_one(
                        {"_id": ObjectId(post_id)},
                        {"$set": {"saves": count}}
                    )
            elif change["operationType"] == "update":
                document_key = change["documentKey"]
                update_description = change["updateDescription"]
                interaction_id = document_key["_id"]

                # Recuperar el documento completo para obtener post_id
                interaction = await interactions_collection.find_one({"_id": interaction_id})
                post_id = interaction["post_id"]

                if "like_date" in update_description.get("updatedFields", {}):
                    count= await count_likes(post_id)
                    await post_collection.update_one(
                        {"_id": ObjectId(post_id)},
                        {"$set": {"likes": count}}
                    )
                if "like_date" in update_description.get("removedFields", []):
                    count= await count_likes(post_id)
                    await post_collection.update_one(
                        {"_id": ObjectId(post_id)},
                        {"$set": {"likes": count}}
                    )
                if "saved_date" in update_description.get("updatedFields", {}):
                    await post_collection.update_one(
                        {"_id": ObjectId(post_id)},
                        {"$set": {"saves": count}}
                    )
                if "saved_date" in update_description.get("removedFields", []):
                    await post_collection.update_one(
                        {"_id": ObjectId(post_id)},
                        {"$set": {"saves": count}}
                    )