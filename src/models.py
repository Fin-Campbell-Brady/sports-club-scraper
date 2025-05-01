from pydantic import BaseModel, Field
from typing import List, Optional, Union

# Pydantic models

# Wikipedia league data

class Clubs(BaseModel):
    club_name: str = Field(..., description="List of clubs name competing in this division")
    wiki_page: Optional[str] = Field(... , description="List of clubs wikipedia page titles competing in the division")

class Division(BaseModel):
    division_name: str = Field(..., description="Name of the division")
    level: Optional[int] = Field(..., description="Tier or level of the division within the league system")
    club: List[Clubs] = Field(..., description="List of clubs and their wiki page title competing in the division")
    number_of_teams: int = Field(..., description="Total number of teams in the division")

class League(BaseModel):
    league_name: str = Field(..., description="Official league name. Don't include the sponsors name")
    number_of_divisions: int = Field(..., description="Number of divisions in the league")
    divisions: List[Division] = Field(..., description="List of divisions within the league")
    governing_body: Optional[str] = Field(None, description="Governing body overseeing the league")
    website_link: Optional[str] = Field(None, description="Official website URL")

# Club Pydanctic models

# Shared club classes 

class SocialMedia(BaseModel):
    Facebook: Optional[str] = Field(None, description="Link to clubs official Facebook")
    Twitter: Optional[str] = Field(None, description="Link to clubs official Twitter")
    Instagram: Optional[str] = Field(None, description="Link to clubs official Instagram")
    TikTok: Optional[str] = Field(None, description="Link to clubs official TikTok")
    YouTube: Optional[str] = Field(None, description="Link to clubs official YouTube")
    Linkedin: Optional[str] = Field(None, description="Link to clubs official Linkedin")

class Location(BaseModel):
    AddressLine1: Optional[str] = Field(None, description="Building name or number of the club's home ground")
    AddressLine2: Optional[str] = Field(None, description="Street address of the club's home ground")
    Town: Optional[str] = Field(None, description="Post town of the club's home ground")
    County: Optional[str] = Field(None, description="County of the club's home ground")
    PostCode: Optional[str] = Field(None, description="Postcode of the club's home ground")
    Country: Optional[str] = Field(None, description="Country of the club's home ground")
    CountryCode: Optional[str] = Field(None, description="Country code of the club's home ground")

# First club pydantic models
# change toooooooo
class LeagueMovement(BaseModel):
    year: Optional[int] = Field(None, description="Year of promotion/relegation")

class Club(BaseModel):
    club_name: Optional[str] = Field(None, description="Official club name")
    social_media: SocialMedia = Field(..., description="The clubs social media links")
    location: Location = Field(..., description="Home ground or stadium of the team location")
    website_link: Optional[str] = Field(None, description="Official website URL")
    promotions: List[LeagueMovement] = Field(..., description="List of promotions with year and league")
    relegations: List[LeagueMovement] = Field(..., description="List of relegations with year and league")
    record_attendance: Optional[int] = Field(None, description="The record attendance")
    year_founded: Optional[int] = Field(None, description="The year the club was founded")
    stadium_capacity: Optional[int] = Field(None, description="Capacity of the main stadium")
    nickname: Optional[str] = Field(None, description="Club nickname (if available)")
    data_availability: Optional[bool] = Field(None, description="Flag indicating if detailed info is available")

# Second club pydantic models

# Club Home page

class ContactInfo(BaseModel):
    contact_label: Optional[str] = Field(None, description="Label for the type of contact (e.g., 'General Inquiries', 'Commercial', 'Enquiries')")
    email: Optional[str] = Field(None, description="Email address for this contact type")
    phone: Optional[str] = Field(None, description="Telephone number for this contact type")

class URLsOfInterest(BaseModel):
    contact_page_url: Optional[Union[List[str], str]] = Field(None, description=("URL(s) leading to the club's contact information page. Commonly labeled as 'Contact', 'Contact Us', or similar. Note: URL structures may vary across different club websites."))
    club_officials_url: Optional[Union[List[str], str]] = Field(None, description=("URL(s) directing to the page listing club officials or management team. Often found under sections like 'Officials', 'Staff', 'Our Team', etc. Be aware that naming conventions and URL patterns can differ between clubs."))

class ClubWebsite(BaseModel):

    club_name: Optional[str] = Field(None, description="Official club name")
    website_url: Optional[str] = Field(None, description="Official website URL of the club")
    urls_of_interest: URLsOfInterest = Field(..., description="The contact and club official")
    contact_info: List[ContactInfo] = Field(..., description="List of contact details for the club, including email addresses and phone numbers for various contact points")
    address: Optional[str] = Field(None, description="Full mailing address for the club")
    social_media: SocialMedia = Field(..., description="The club's social media links")
    home_ground: Location = Field(None, description="Home ground or stadium of the team location")
    competitor: Optional[str] = Field(None, description="Name of the competitor providing website services (e.g., Touchline, Pitchero, MyClubPro)")


# Fourth pydantic model

# Club URLs of interest
# Change to make more general both these and urls of interest


class ClubOfficial(BaseModel):
    first_name: Optional[str] = Field(None, description="Official's first name")
    last_name: Optional[str] = Field(None, description="Official's last name")
    telephone: Optional[str] = Field(None, description="Official's phone number")
    email: Optional[str] = Field(None, description="Official's email address")
    role: Optional[str] = Field(None, description="Official's role (e.g., Chairman / President / Vice / Club Secutary / )")

class ClubOfficialAndContact(BaseModel):
    contact_info: List[ContactInfo] = Field(..., description="Club's contact details (emails, phone numbers)")
    location: Location = Field(..., description="Club's stadium or ground location")
    officials: Union[List[ClubOfficial], str] = Field(..., description="List of club officials with their roles")
    contact_form: bool = Field(..., description="Indicates presence of a contact form on the page")
