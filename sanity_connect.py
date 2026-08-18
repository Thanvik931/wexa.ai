import os
from dotenv import load_dotenv
from neo4j import GraphDatabase

load_dotenv()

driver = GraphDatabase.driver(
    os.environ["COGNODB_URI"],
    auth=(os.environ["COGNODB_USER"], os.environ["COGNODB_PASSWORD"]),
)
driver.verify_connectivity()
print("Connected successfully")
