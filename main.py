import uvicorn
import asyncio
from dub import Dub
from fastapi import FastAPI, HTTPException, Query
from pydantic import BaseModel, HttpUrl
import instaloader
import os
from dotenv import load_dotenv
import httpx

app = FastAPI()

load_dotenv()

# Initialize Dub client
dub_client = Dub(token=os.getenv("DUB_TOKEN"))

BRIGHTDATA_API_KEY = os.getenv("BRIGHTDATA_API_KEY")
BRIGHTDATA_DATASET_ID = os.getenv("BRIGHTDATA_DATASET_ID")

class ProfileRequest(BaseModel):
    username: str

class ProfileResponse(BaseModel):
    username: str
    full_name: str
    biography: str
    profile_pic_url: str
    is_private: bool
    followers_count: int
    followees_count: int
    media_count: int
    user_id: int
    is_verified: bool

class URLRequest(BaseModel):
    url: HttpUrl

@app.post("/profile", response_model=ProfileResponse)
async def get_profile(request: ProfileRequest):
    try:
        L = instaloader.Instaloader()
        profile = instaloader.Profile.from_username(L.context, request.username)
        
        return ProfileResponse(
            username=profile.username,
            full_name=profile.full_name,
            biography=profile.biography,
            profile_pic_url=profile.profile_pic_url,
            is_private=profile.is_private,
            followers_count=profile.followers,
            followees_count=profile.followees,
            media_count=profile.mediacount,
            user_id=profile.userid,
            is_verified=profile.is_verified
        )
    except instaloader.exceptions.ProfileNotExistsException:
        raise HTTPException(status_code=404, detail="Profile not found")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/create-link")
async def create_link(url: HttpUrl = Query(..., description="The URL to be shortened")):
    try:
        response = dub_client.links.create(request={
            "url": str(url)
        })
        
        if response is not None:
            return response
        else:
            raise HTTPException(status_code=500, detail="Failed to create link")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/get-user-profile")
async def get_instagram_profile(request: URLRequest):
    headers = {
        "Authorization": f"Bearer {BRIGHTDATA_API_KEY}",
        "Content-Type": "application/json"
    }
    
    data = [{"url": str(request.url)}]
    
    async with httpx.AsyncClient() as client:
        try:
            response = await client.post(
                f"https://api.brightdata.com/datasets/v3/trigger?dataset_id={BRIGHTDATA_DATASET_ID}",
                headers=headers,
                json=data
            )
            response.raise_for_status()
            data = response.json()

            snapshot_id = data.get("snapshot_id")
            if not snapshot_id:
                raise HTTPException(status_code=500, detail="Failed to get snapshot_id from Brightdata")
            # wait for 5 seconds
            await asyncio.sleep(5)
            snapshot_data = await get_brightdata_snapshot(snapshot_id)
            
            return snapshot_data
        except httpx.HTTPStatusError as e:
            raise HTTPException(status_code=e.response.status_code, detail=str(e))
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))

@app.get("/analytics")
async def retrieve_analytics(link_id: str = Query(..., description="The ID of the link to retrieve analytics for")):
    try:
        response = dub_client.analytics.retrieve(request={
            "link_id": link_id
        })
        
        if response is not None:
            return response
        else:
            raise HTTPException(status_code=500, detail="Failed to retrieve analytics")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/brightdata-snapshot")
async def get_brightdata_snapshot(snapshot_id: str = Query(..., description="The ID of the Brightdata snapshot")):
    headers = {
        "Authorization": f"Bearer {BRIGHTDATA_API_KEY}",
    }
    
    async with httpx.AsyncClient() as client:
        try:
            response = await client.get(
                f"https://api.brightdata.com/datasets/v3/snapshot/{snapshot_id}?format=json",
                headers=headers
            )
            response.raise_for_status()
            return response.json()
        except httpx.HTTPStatusError as e:
            raise HTTPException(status_code=e.response.status_code, detail=str(e))
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))


if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)