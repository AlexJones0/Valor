import sqlite3
from encryption import EncryptText, DecryptText
from time import time as CurrentTime
import config
global database


class Database:
    """ A class used to represent a loaded/created database, interacted with
        using SQL commands using the sqlite3 python mo`d`ule."""
    def __init__(self, name):
        """ The constructor for the Database class. Loads and connects to the
            database with the given name, whether it exists or not.
              Inputs: name (a string that details the filename (and/or relative
            path) of the database file).
              Outputs: None."""
        if not name.endswith(".db"):
            name += ".db"
        self.name = name
        self.__connection = sqlite3.connect(self.name)
        self.__cursor = self.__connection.cursor()
        self.connected = True

    @property
    def exists(self):
        """ A property that returns a Boolean value that describes whether a
            database with the given name actually exists, so that it can be
            created if it does not. No inputs, Boolean output."""
        # retrieve list of names of tables that exist
        tables = self.Query("SELECT name FROM sqlite_master")
        return len(tables) > 0

    def Query(self, query, parameters=None):
        """ This method is used to perform an SQL query on the database,
            allowing alteration of the database, retrieval of data etc.
              Inputs: query (a string/docstring containing the SQL statement to
            be executed, as well as '?' symbols for any parameters to be
            replaced) and parameters (a list or tuple of values that are used to
            fill any '?' parameter spaces within the given SQL query).
              Outputs: any results of the SQL query, in the form of a tuple
            containing the queried information."""
        if not self.connected:
            return
        if parameters is None:
            self.__cursor.execute(query)
        else:
            self.__cursor.execute(query, parameters)
        return self.__cursor.fetchall()

    def CommitChanges(self):
        """ Actually commits any changes to the database made by SQL queries so
            that they will take effect on the actual database.
              Inputs: None.
              Outputs: None."""
        self.__connection.commit()

    def QueryAndCommit(self, query, arguments=None):
        result = self.Query(query, arguments)
        self.CommitChanges()
        return result

    @property
    def lastrowid(self):
        """ Returns the id (primary key integer) of the last row accessed by
            the cursor.
              Inputs: None.
              Outputs: An integer (or None) representing the primary key integer
            ID of the last row accessed by the cursor (of the last table
            accessed by the cursor)."""
        return self.__cursor.lastrowid

    def Close(self):
        """ This method closes the database connection so that you are no longer
            connected to the database and no more queries/requests can be used
            on the database.
              Inputs: None.
              Outputs: None."""
        self.__connection.close()
        self.connected = False

    def __del__(self):
        """Ensures that when the database object is deleted, its connection is
           first closed beforehand."""
        self.Close()


def CreateDatabase():
    global database
    database.QueryAndCommit("""CREATE TABLE Tags (
        TagID INTEGER NOT NULL,
        Name TEXT NOT NULL,
        Description TEXT,
        PRIMARY KEY (TagID)
        )""")
    database.QueryAndCommit("""CREATE TABLE IgnoredTags (
        Name TEXT NOT NULL,
        PRIMARY KEY (Name)
    )""")
    database.QueryAndCommit(
        """CREATE TABLE Synonyms (
        SynID INTEGER NOT NULL,
        TagID INTEGER NOT NULL,
        Synonym TEXT NOT NULL,
        PRIMARY KEY (SynID),
        FOREIGN KEY (TagID) REFERENCES Tags (TagID)
        ON UPDATE CASCADE ON DELETE CASCADE
        )"""
    )  # the SynID primary key only exists so synonyms can be ordered by the order they were added. Literally no other reason.
    database.QueryAndCommit("""CREATE TABLE Items (
        ItemID INTEGER NOT NULL,
        ItemText TEXT NOT NULL,
        Description TEXT,
        TimesServed INTEGER NOT NULL,
        TimeAdded TIME,
        TimeLastUpdated TIME,
        Score INTEGER NOT NULL,
        Rating INTEGER,
        PRIMARY KEY (ItemID)
        )""")
    database.QueryAndCommit("""CREATE TABLE ItemTags (
        ItemID INTEGER NOT NULL,
        TagID INTEGER NOT NULL,
        FOREIGN KEY (ItemID) REFERENCES Items (ItemID)
        ON UPDATE CASCADE ON DELETE CASCADE,
        FOREIGN KEY (TagID) REFERENCES Tags (TagID)
        ON UPDATE CASCADE ON DELETE CASCADE
        )""")
    database.QueryAndCommit("""CREATE TABLE Searches (
        SearchID INTEGER NOT NULL,
        Name TEXT NOT NULL,
        SearchText TEXT NOT NULL,
        Type TEXT,
        Format TEXT,
        PRIMARY KEY (SearchID)
    )""")


def LoadDatabase(database_path):
    global database
    try:
        database = Database(database_path)
        if not database.exists:
            CreateDatabase()
    except:
        database = Database(database_path)
        CreateDatabase()


def AddTag(name, description, synonyms):
    global database
    name = EncryptText(config.settings["key"], name)
    description = EncryptText(config.settings["key"], description)
    database.QueryAndCommit(
        """INSERT INTO Tags (Name, Description) 
           VALUES (?, ?)""", (name, description))
    tag_id = database.lastrowid
    if synonyms == None:
        return
    for synonym in synonyms:
        synonym = EncryptText(config.settings["key"], synonym)
        database.QueryAndCommit(
            """INSERT INTO Synonyms (TagID, Synonym) 
               VALUES (?, ?)""", (tag_id, synonym))
    return tag_id


def AddItem(text, desc, times_served, time_added, time_last_updated, score,
            rating, tags):
    text = EncryptText(config.settings["key"], text)
    desc = EncryptText(config.settings["key"], desc)
    database.QueryAndCommit(
        """INSERT INTO Items (ItemText, Description, TimesServed, TimeAdded, TimeLastUpdated, Score, Rating)
           VALUES (?, ?, ?, ?, ?, ?, ?)""",
        (text, desc, times_served, time_added, time_last_updated, score,
         rating))
    item_id = database.lastrowid
    if tags == None:
        return
    current_tags = GetTagNamesAndIDs(dict_form=True)
    for tag in tags:
        tag_id = current_tags[tag]
        database.QueryAndCommit(
            """INSERT INTO ItemTags (ItemID, TagID)
               VALUES (?, ?)""", (item_id, tag_id))


def FindReplicaTags(name, synonyms=None, exclude=None):
    global database
    if synonyms == None:
        synonyms = []
    if exclude == None:
        exclude = []
    to_search = [name] + synonyms
    for item in to_search:
        enc_item = EncryptText(config.settings["key"], item)
        matches = database.Query(
            """SELECT COUNT(*)
               FROM Tags
               WHERE Name = ?""", (enc_item, ))[0][0]
        if matches > 0 and item not in exclude:
            return (item, item, "name")
        matches = database.Query(
            """SELECT Tags.Name
               FROM Tags
               INNER JOIN Synonyms ON Tags.TagID = Synonyms.TagID
               WHERE Synonyms.Synonym = ?""", (enc_item, ))
        if len(matches) > 0:
            if len(exclude) > 0:
                for m in matches:
                    match_name = DecryptText(config.settings["key"], m[0])
                    if match_name not in exclude:
                        return (item, match_name, "synonym")
            else:
                match_name = DecryptText(config.settings["key"], matches[0][0])
                return (item, match_name, "synonym")
    return None


def GetSuggestedSynonyms(phrases, exclude=None):
    global database
    if exclude == None:
        exclude = []
    suggestions = []
    for phrase_info in phrases:
        phrase = EncryptText(config.settings["key"], phrase_info[0])
        start = phrase_info[1]
        end = phrase_info[2]
        matches = database.Query(
            """SELECT Synonyms.Synonym, Tags.Name
               FROM Synonyms
               INNER JOIN Tags on Synonyms.TagID = Tags.TagID
               WHERE Tags.Name = ?
               ORDER BY Synonyms.SynID ASC""", (phrase, ))
        if len(matches) > 0:  # i.e. synonyms found therefore matches tag name
            if len(exclude) > 0:
                do_continue = False
                for m in matches:
                    name = DecryptText(config.settings["key"], m[1])
                    if name not in exclude:
                        synonym = DecryptText(config.settings["key"], m[0])
                        suggestions.append([synonym, start, end])
                        do_continue = True
                if do_continue:
                    continue
            else:
                suggestions += [[
                    DecryptText(config.settings["key"], i[0]), start, end
                ] for i in matches]
                continue
        matches = database.Query(
            """SELECT Synonyms.TagID, Tags.Name
               FROM Synonyms
               INNER JOIN Tags on Synonyms.TagID = Tags.TagID
               WHERE Synonyms.Synonym = ?
               ORDER BY Synonyms.SynID ASC""", (phrase, ))
        if len(matches) == 0:  # i.e. not found as a synonym
            continue
        else:
            do_continue = False
            for m in matches:
                name = DecryptText(config.settings["key"], m[1])
                # TODO check changed so not sure if this broke something
                if name in exclude:
                    do_continue = True
            if do_continue:
                continue
        # if the code below runs, it was found as a synonym.
        tag_id = matches[0][0]
        matches = database.Query(
            """SELECT Synonyms.Synonym
               FROM Synonyms
               WHERE Synonyms.TagID = ?
               AND Synonyms.Synonym <> ?
               ORDER BY Synonyms.SynID ASC""", (tag_id, phrase))
        suggestions += [[
            DecryptText(config.settings["key"], i[0]), start, end
        ] for i in matches]
        matches = database.Query(
            """SELECT Tags.Name
               FROM Tags
               WHERE Tags.TagID = ?""", (tag_id, ))
        suggestions.append(
            [DecryptText(config.settings["key"], matches[0][0]), start, end])
    return suggestions


def GetAllTagData(return_dict=False):
    # TODO change to a more efficient method (e.g. see GetAllItemData below)
    global database
    tag_data = {}
    db_data = database.Query(
        """SELECT Tags.TagID, Tags.Name, Tags.Description, Synonyms.Synonym
           FROM TAGS
           LEFT JOIN Synonyms ON Tags.TagID = Synonyms.TagID
           ORDER BY Tags.TagID ASC""")
    for info in db_data:
        id_ = info[0]
        name = DecryptText(config.settings["key"], info[1])
        desc = info[2]
        if desc != None:
            desc = DecryptText(config.settings["key"], desc)
        synonym = info[3]
        if synonym != None:
            synonym = DecryptText(config.settings["key"], synonym)
        if id_ not in tag_data:
            tag_data[id_] = [name, desc, []]
            if synonym != None:
                tag_data[id_][2].append(synonym)
        elif synonym != None:
            tag_data[id_][2].append(synonym)
    if return_dict:
        return tag_data
    return list(tag_data.values())


def GetAllItemData(return_dict=False):
    global database
    item_data = {}
    db_data = database.Query(
        """SELECT Items.ItemID, Items.ItemText, Items.Description, Items.TimesServed, Items.TimeAdded, Items.TimeLastUpdated, Items.Score, Items.Rating
           FROM ITEMS
           ORDER BY Items.ItemID ASC""")
    tags_data = database.Query("""SELECT Items.ItemID, Tags.Name
           FROM Items
           LEFT JOIN ItemTags on Items.ItemID = ItemTags.ItemID
           LEFT JOIN Tags on ItemTags.TagID = Tags.TagID
           Order by Items.ItemID ASC""")
    item_tags = {}
    for tag_info in tags_data:
        id_ = tag_info[0]
        if id_ not in item_tags.keys():
            item_tags[id_] = [tag_info[1]]
        else:
            item_tags[id_].append(tag_info[1])
    for info in db_data:
        id_ = info[0]
        text = DecryptText(config.settings["key"], info[1])
        desc = info[2]
        if desc != None:
            desc = DecryptText(config.settings["key"], desc)
        times_served = info[3]
        time_added = info[4]
        time_last_updated = info[5]
        score = info[6]
        rating = info[7]
        tags = item_tags[id_]
        for i, tag in enumerate(tags):
            if tag != None:
                tags[i] = DecryptText(config.settings["key"], tag)
        item_data[id_] = [
            text, desc, times_served, time_added, time_last_updated, score,
            rating, tags
        ]
    if return_dict:
        return item_data
    return list(item_data.values())


def GetAllItemTags():
    global database
    db_data = database.Query("""SELECT Items.ItemID, ItemTags.TagID
           FROM Items
           LEFT JOIN ItemTags on Items.ItemID = ItemTags.ItemID""")
    item_data = {}
    for info in db_data:
        id_ = info[0]
        tag = info[1]
        if id_ not in item_data:
            if tag == None:
                item_data[id_] = []
            else:
                item_data[id_] = [tag]
        elif tag != None:
            item_data[id_].append(tag)
    to_return = []
    for item in item_data.keys():
        to_return.append([item, item_data[item]])
    return to_return


def GetTagData(tag_name):
    global database
    tag_data = {}
    enc_name = EncryptText(config.settings["key"], tag_name)
    data = database.Query(
        """SELECT Tags.Description, Synonyms.Synonym
           FROM TAGS
           LEFT JOIN Synonyms ON Tags.TagID = Synonyms.TagID
           WHERE Tags.Name = ?
           ORDER BY Synonyms.SynID ASC""", (enc_name, ))
    if len(data) == 0:
        return None
    tag_data["NAME"] = tag_name
    if data[0][0] != None:
        tag_data["DESCRIPTION"] = DecryptText(config.settings["key"],
                                              data[0][0])
    else:
        tag_data["DESCRIPTION"] = data[0][0]
    tag_data["SYNONYMS"] = []
    if len(data) == 1:
        synonym = data[0][1]
        if synonym != None:
            synonym = DecryptText(config.settings["key"], synonym)
            tag_data["SYNONYMS"].append(synonym)
    else:
        for record in data:
            synonym = DecryptText(config.settings["key"], record[1])
            tag_data["SYNONYMS"].append(synonym)
    return tag_data


def GetItemTextFromID(item_id):
    global database
    data = database.Query(
        """SELECT ItemText
           FROM Items
           WHERE ItemID = ?""", (item_id, ))
    if len(data) == 0:
        return None
    else:
        text = DecryptText(config.settings["key"], data[0][0])
        return text


def GetTagDataFromSynonym(synonym):
    global database
    synonym = EncryptText(config.settings["key"], synonym)
    data = database.Query(
        """SELECT Tags.Name
           FROM TAGS
           INNER JOIN Synonyms ON Tags.TagID = Synonyms.TagID
           WHERE Synonyms.Synonym = ?""", (synonym, ))
    if len(data) == 0:
        return None
    else:
        tag_name = DecryptText(config.settings["key"], data[0][0])
        return GetTagData(tag_name)


def GetTagIDsFromNames(tags):
    import fnmatch
    tags_data = GetAllTagData(return_dict=True)
    tag_ids = {}
    for tag in tags:
        if "*" in tag:
            added = 0
            for s_tag in tags_data.keys():
                data = tags_data[s_tag]
                if config.settings["check_synonyms_for_wildcards"]:
                    to_check = [data[0]] + data[2]
                else:
                    to_check = [data[0]]
                if len(fnmatch.filter(to_check, tag)) > 0:
                    if added == 0:
                        tag_ids[tag] = [s_tag]
                    else:
                        tag_ids[tag].append(s_tag)
                    added += 1
        else:
            for s_tag in tags_data:
                data = tags_data[s_tag]
                if data[0] == tag or (data[2] != None and tag in data[2]):
                    tag_ids[tag] = s_tag
                    break
    return tag_ids


def GetTagID(text):
    global database
    text = EncryptText(config.settings["key"], text)
    data = database.Query(
        """SELECT Tags.ID
           FROM TAGS
           INNER JOIN Synonyms ON Tags.TagID = Synonyms.TagID
           WHERE Synonyms.Synonym = ? OR Tags.Name = ? """, (text, text))
    if len(data) == 0:
        return None
    else:
        return data[0][0]


def GetItemNames():
    global database
    return [
        DecryptText(config.settings["key"], i[0])
        for i in database.Query("""SELECT ItemText FROM Items""")
    ]


def GetTagNames():
    global database
    return [
        DecryptText(config.settings["key"], i[0])
        for i in database.Query("""SELECT Name FROM Tags""")
    ]


def GetTagNamesAndIDs(dict_form=True):
    global database
    data = database.Query("""SELECT Name, TagID FROM Tags""")
    if dict_form:
        new_data = {}
        for i in data:
            new_data[DecryptText(config.settings["key"], i[0])] = i[1]
        return new_data
    else:
        data = [[DecryptText(config.settings["key"], i[0]), i[1]]
                for i in data]
        return data


def GetIgnoredTags():
    global database
    return [
        DecryptText(config.settings["key"], i[0])
        for i in database.Query("""SELECT Name FROM IgnoredTags""")
    ]


def AddIgnoredTag(tag):
    global database
    database.QueryAndCommit("""INSERT INTO IgnoredTags (Name) VALUES (?)""",
                            (EncryptText(config.settings["key"], tag), ))


def RemoveIgnoredTag(tag):
    global database
    tag = EncryptText(config.settings["key"], tag)
    #  bugged, not sure why it is not removing right now. COMEHERE todo fix.
    database.QueryAndCommit("DELETE FROM IgnoredTags WHERE Name = ?", (tag, ))


def RemoveTag(tag):
    global database
    tag = EncryptText(config.settings["key"], tag)
    database.QueryAndCommit("DELETE FROM Tags WHERE Name = ?", (tag, ))


def RemoveTags(tags):
    for tag in tags:
        RemoveTag(tag)


def UpdateTag(old_name, old_synonyms, name, desc, synonyms):
    global database
    old_name = EncryptText(config.settings["key"], old_name)
    name = EncryptText(config.settings["key"], name)
    if desc != None:
        desc = EncryptText(config.settings["key"], desc)
    database.QueryAndCommit(
        """UPDATE Tags
           SET Name=?, Description=?
           WHERE Tags.Name = ?""", (name, desc, old_name))
    # TODO check: not sure why, but tag_id = database.lastrowid was throwing up errors here.
    # so for now, just the less efficient way.
    tag_id = database.Query(
        """SELECT TagID
           FROM Tags
           WHERE Tags.Name = ?""", (name, ))[0][0]
    for s in old_synonyms:
        if s not in synonyms:
            s = EncryptText(config.settings["key"], s)
            database.QueryAndCommit(
                """DELETE FROM Synonyms 
                   WHERE Synonym=?""", (s, ))
    for s in synonyms:
        if s not in old_synonyms:
            s = EncryptText(config.settings["key"], s)
            database.QueryAndCommit(
                """INSERT INTO Synonyms (TagID, Synonym) 
                   VALUES (?, ?)""", (tag_id, s))


def GetFirstTags(amount):
    global database
    tags = database.Query(
        """ SELECT Name
            FROM TAGS
            ORDER BY TagId ASC
            LIMIT ?""", (amount, ))
    if len(tags) == 0:
        return []
    return [DecryptText(config.settings["key"], tag[0]) for tag in tags]
