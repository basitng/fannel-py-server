from typing import Optional
from dub import Dub
from fastapi import FastAPI, HTTPException, Query
from pydantic import BaseModel, HttpUrl
import instaloader
import os
from dotenv import load_dotenv
app = FastAPI()

load_dotenv()

# Initialize Dub client
dub_client = Dub(token=os.getenv("DUB_TOKEN"))

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

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)