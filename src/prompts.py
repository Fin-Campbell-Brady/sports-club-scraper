import os
from langchain_openai import ChatOpenAI
from langchain import PromptTemplate
from langchain.output_parsers import PydanticOutputParser

import pydantic_models
from pydantic_models import League, Club, ClubWebsite, ClubOfficialAndContact


OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")


llm = ChatOpenAI(model_name="gpt-4o-mini", openai_api_key=OPENAI_API_KEY, temperature = 0)


# First prompt

# Wikipedia league prompt

parser_league = PydanticOutputParser(pydantic_object=League)

prompt_league = PromptTemplate(template=
""" {wikipedia_data_league}

You must only answer the question based on the context provided, if the information is not present then you must say that.

    I'm trying to gather together information from wikipedia on different football leagues in England.

    Your task is to provide the specified information about the "{league_name}" based on this data and this data alone. If the information is not available you must must must say.

    You must provide the informaton in the format below:

        {format_instructions}
    """,
    input_variables=["league_name", "wikipedia_data_league"],
    partial_variables={"format_instructions": parser_league.get_format_instructions()})


chain_league = prompt_league | llm


# Second prompt

# Wiki Club 

parser_club = PydanticOutputParser(pydantic_object=Club)

prompt_club = PromptTemplate(template=
""" {wikipedia_data_club}

You must only answer the question based on the context provided, if the information is not present then you must say that.

    I'm trying to gather together information from wikipedia on different football clubs/team in England.

    Your task is to provide the specified information about the football club "{club_name}" based on this data and this data alone. If the information is not available you must must must say.


        {format_instructions}
    """,
    input_variables=["club_name", "wikipedia_data_club"],
    partial_variables={"format_instructions": parser_club.get_format_instructions()})

chain_club = prompt_club | llm 

# Third prompt

# Club Home page

parser_ClubWebsite = PydanticOutputParser(pydantic_object=ClubWebsite)

prompt_ClubWebsite = PromptTemplate(template=
""" Existing Wikipedia data:
{wikipedia_data_club}

Website HTML data:

{club_website_html}

You must only answer the question based on the context provided, if the information is not present then you must say that.

    I'm trying to gather together information from a clubs website and the partially completed json object.

    Your task is to provide the specified information about the club based on this data and this data alone. If the information is not available you must must must say.


        {format_instructions}
    """,
    input_variables=["club_website_html", "wikipedia_data_club"],
    partial_variables={"format_instructions": parser_ClubWebsite.get_format_instructions()})

chain_ClubWebsite = prompt_ClubWebsite | llm

# Fourth Prompt

# Club URLs of interest

parser_ClubOfficialAndContact = PydanticOutputParser(pydantic_object=ClubOfficialAndContact)

prompt_club_official_and_contact = PromptTemplate(template=
""" 
{official_club_website_html}

You must only answer the question based on the context provided, if the information is not present then you must say that.

    I'm trying to gather together information from a clubs website.

    Your task is to provide the specified information about the club based on this data and this data alone. If the information is not available you must must must say.


        {format_instructions}
    """,
    input_variables=["official_club_website_html"],
    partial_variables={"format_instructions": parser_ClubOfficialAndContact.get_format_instructions()})

chain_ClubOfficialAndContact = prompt_club_official_and_contact | llm