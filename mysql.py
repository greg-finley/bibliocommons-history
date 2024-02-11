import json
import os
from typing import NamedTuple

import mysql.connector

from main import User


class LatestCount(NamedTuple):
    person: str
    type: str
    item_count: int


class MySQLClient:
    #   CREATE TABLE `library_item_count` (
    # 	`id` int NOT NULL AUTO_INCREMENT,
    # 	`person` varchar(300) NOT NULL,
    # 	`type` varchar(300) NOT NULL,
    # 	`item_count` mediumint unsigned NOT NULL,
    # 	PRIMARY KEY (`id`),
    # 	UNIQUE KEY `person_type` (`person`, `type`)
    # ) ENGINE InnoDB,
    #   CHARSET utf8mb4,
    #   COLLATE utf8mb4_0900_ai_ci;
    def __init__(self) -> None:
        config = json.loads(os.environ["MYSQL_CONFIG"])
        self.conn = mysql.connector.connect(
            host=config["MYSQL_HOST"],
            user=config["MYSQL_USERNAME"],
            passwd=config["MYSQL_PASSWORD"],
            database=config["MYSQL_DATABASE"],
            ssl_ca=os.environ.get(
                "SSL_CERT_FILE", "/etc/ssl/certs/ca-certificates.crt"
            ),
        )
        self.conn.autocommit = True  # type: ignore

    def get_latest_counts(self) -> list[LatestCount]:
        cursor = self.conn.cursor(dictionary=True)
        cursor.execute("SELECT person, type, item_count FROM library_item_count")
        results = cursor.fetchall()
        cursor.close()
        return [LatestCount(**r) for r in results]  # type: ignore

    def upsert_count(self, user: User, new_count: int) -> None:
        cursor = self.conn.cursor()
        cursor.execute(
            "INSERT INTO library_item_count (person, type, item_count) VALUES (%s, %s, %s) ON DUPLICATE KEY UPDATE item_count = %s",
            (user["name"], user["type"], new_count, new_count),
        )
        cursor.close()

    def close(self) -> None:
        self.conn.close()
