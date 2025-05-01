import pyodbc
from decimal import Decimal
import os

SERVER   = os.getenv("DB_SERVER")    
DATABASE = os.getenv("DB_NAME")      
UID      = os.getenv("DB_USER")     
PWD      = os.getenv("DB_PASSWORD")  

CONN_STR = (
    f"DRIVER={{ODBC Driver 18 for SQL Server}};"
    f"SERVER={SERVER};DATABASE={DATABASE};"
    f"UID={UID};PWD={PWD};Trusted_Connection=yes;"
)

def connect_db():
    """
    Returns a new pyodbc.Connection using environment-driven credentials.
    All of your existing functions should call this instead of hard‐coded connect strings.
    """
    try:
        conn = pyodbc.connect(CONN_STR)
        return conn
    except pyodbc.Error as e:
        logger.error(f"Unable to connect to database: {e}")
        raise


# First insert information related to the league

def insert_league_with_divisions(league, wiki_link):

    conn = connect_db() 
    cur = conn.cursor()
    try:
        cur.execute("INSERT INTO dbo.League (LeagueName, NumberOfDivisions, GoverningBody, WikiLink) OUTPUT INSERTED.LeagueID VALUES (?, ?, ?, ?);",
                    (league.league_name, league.number_of_divisions, league.governing_body, wiki_link, league.website_link))
        league_id = cur.fetchone()[0]

        division_ids = []

        for d in league.divisions:
            cur.execute("INSERT INTO dbo.Division (DivisionName, TierLevel, NumberOfTeams, LeagueID) OUTPUT INSERTED.DivisionID VALUES (?, ?, ?, ?);",
                        (d.division_name, d.level, d.number_of_teams, league_id))
            division_ids.append(cur.fetchone()[0])

        conn.commit() 
        logger.info(f"Added LeagueID={league_id} DivisionIDs={division_ids}") 
        return {"message": "Insert successful", "LeagueID": league_id, "DivisionIDs": division_ids}

    except pyodbc.Error as db_err:
        conn.rollback() 
        logger.error(f"DB error: {db_err}")
        return {"error": "Database operation failed."}

    except Exception as ex:
        conn.rollback() 
        logger.error(f"Unexpected error: {ex}")
        return {"error": "An unexpected error occurred."}

    finally:
        cur.close() 
        conn.close()



def add_location_and_club(data):

    conn = connect_db()
    cur = conn.cursor()
    try:
        
        cur.execute(
            "INSERT INTO dbo.Locations ""(AddressLine1, AddressLine2, Town, County, PostCode, Country, CountryCode, GeoPoint) ""OUTPUT INSERTED.LocationID ""VALUES (?, ?, ?, ?, ?, ?, ?, geography::STPointFromText(?, 4326));",
            (data["AddressLine1"], data.get("AddressLine2"), data["Town"], data.get("County"), data.get("PostCode"), data.get("Country"), data.get("CountryCode"), data["GeoWKT"]))
        location_id = cur.fetchone()[0]
        logger.info(f"Inserted LocationID={location_id}")

        cur.execute("INSERT INTO dbo.Clubs ""(ClubName, RecordAttendance, YearFounded, StadiumCapacity, Nickname, LocationID, CompetitorID) ""OUTPUT INSERTED.ClubID ""VALUES (?, ?, ?, ?, ?, ?, ?);",
            (data["ClubName"], data.get("RecordAttendance"), data.get("YearFounded"), data.get("StadiumCapacity"), data.get("Nickname"), location_id)
        )
        club_id = cur.fetchone()[0]
        logger.info(f"Inserted ClubID={club_id}")

        conn.commit()
        return club_id

    except pyodbc.Error as db_err:
        logger.error(f"DB error in add_location_and_club: {db_err}")
        conn.rollback()
        return {"error": "Database operation failed."}

    except Exception as ex:
        logger.error(f"Unexpected error in add_location_and_club: {ex}")
        conn.rollback()
        return {"error": "An unexpected error occurred."}

    finally:
        cur.close()
        conn.close()



def add_club_details(data, club_id):

    try:
        conn = connect_db()
        cur = conn.cursor()

        insert_club_website = '''
            INSERT INTO dbo.ClubWebsites (ClubID, WikiPageURL, HomePageURL, ContactPageURL, OfficialPageURL)
            VALUES (?, ?, ?, ?, ?);
        '''
        cursor.execute(insert_club_website, (club_id, data.get("WikiPageURL"), data.get("HomePageURL"), data.get("ContactPageURL"), data.get("OfficialPageURL")))

        insert_social_media = '''
            INSERT INTO dbo.SocialMedia (ClubID, Facebook, Twitter, Instagram, Tiktok, Youtube, Linkedin)
            VALUES (?, ?, ?, ?, ?, ?, ?);
        '''
        cursor.execute(insert_social_media, (club_id, data.get("Facebook"), data.get("Twitter"), data.get("Instagram"), data.get("Tiktok"), data.get("Youtube"), data.get("Linkedin")))

        insert_club_contact = '''
            INSERT INTO dbo.ClubContacts (ClubID, FirstName, LastName, Telephone, Email, Role)
            OUTPUT INSERTED.ContactID
            VALUES (?, ?, ?, ?, ?, ?);
        '''
        cursor.execute(insert_club_contact, (club_id, data.get("FirstName"), data.get("LastName"), data.get("Telephone"), data.get("Email"), data.get("Role")))
        contact_id = cursor.fetchone()[0]

        connection.commit()
        logging.info(f"Successfully added club details for ClubID: {data['ClubID']}")
        return {"message": "Club details added successfully", "ClubID": data["ClubID"], "ContactID": contact_id}

    except pyodbc.Error as e:
        logging.error(f"Database error in add_club_details: {e}")
        if connection:
            connection.rollback()
        return {"error": "Database operation failed."}

    except Exception as e:
        logging.error(f"Unexpected error in add_club_details: {e}")
        if connection:
            connection.rollback()
        return {"error": "An unexpected error occurred."}

    finally:
        cur.close()
        conn.close()



def add_movement_and_division_club(data: dict) -> dict:

    conn = connect_db()
    cur = conn.cursor()
    try:
        cur.execute(
            "INSERT INTO dbo.LeagueMovements (ClubID, Year, MovementType) "
            "OUTPUT INSERTED.MovementID VALUES (?, ?, ?);",
            (data["ClubID"], data["Year"], data["MovementType"])
        )
        movement_id = cur.fetchone()[0] 
        logger.info(f"Inserted MovementID={movement_id}")

        cur.execute(
            "INSERT INTO dbo.Division_Clubs (DivisionID, ClubID) VALUES (?, ?);",
            (data["DivisionID"], data["ClubID"])
        )
        logger.info(f"Linked DivisionID={data['DivisionID']} with ClubID={data['ClubID']}")

        
        conn.commit()  
        return {"message": "Insert successful", "MovementID": movement_id}

    except pyodbc.Error as db_err:
        logger.error(f"Database error: {db_err}")
        conn.rollback()
        return {"error": "Database operation failed."}

    except Exception as ex:
        logger.error(f"Unexpected error: {ex}")
        conn.rollback()
        return {"error": "An unexpected error occurred."}

    finally:
        cur.close()
        conn.close()