-- ChatRoom definition

CREATE TABLE ChatRoom (
    seq INTEGER PRIMARY KEY AUTOINCREMENT,
    id TEXT UNIQUE,
    name TEXT,
    prompt TEXT,
    created_at TEXT NOT NULL DEFAULT (DATETIME('now', 'localtime')),
    updated_at TEXT NOT NULL DEFAULT (DATETIME('now', 'localtime'))
);

-- Message definition

CREATE TABLE Message (
    chat_id TEXT,
    --  In SQLite, the AUTOINCREMENT keyword can only be used with INTEGER PRIMARY KEY.
    seq INTEGER PRIMARY KEY AUTOINCREMENT,
    id TEXT UNIQUE,
    from_who TEXT,
    msg TEXT,
    created_at TEXT NOT NULL DEFAULT (DATETIME('now', 'localtime')),
    updated_at TEXT NOT NULL DEFAULT (DATETIME('now', 'localtime')),
    FOREIGN KEY (chat_id) REFERENCES ChatRoom(id) ON DELETE CASCADE ON UPDATE CASCADE
);
           
-- Code definition

CREATE TABLE Code (
    seq INTEGER PRIMARY KEY AUTOINCREMENT,
    id TEXT UNIQUE,
    category VARCHAR NOT NULL, 
    value VARCHAR NOT NULL, 
    created_at TEXT NOT NULL DEFAULT (DATETIME('now', 'localtime')),
    updated_at TEXT NOT NULL DEFAULT (DATETIME('now', 'localtime'))
);

-- Update Trigger definition

CREATE TRIGGER trigger_entityintent_updated_at AFTER UPDATE ON Code
            BEGIN
                UPDATE Code SET updated_at = DATETIME('now', 'localtime') WHERE rowid == NEW.rowid;
            END;
            
CREATE TRIGGER trigger_chatroom_updated_at AFTER UPDATE ON ChatRoom
            BEGIN
                UPDATE ChatRoom SET updated_at = DATETIME('now', 'localtime') WHERE rowid == NEW.rowid;
            END;

CREATE TRIGGER trigger_message_updated_at AFTER UPDATE ON Message
            BEGIN
                UPDATE Message SET updated_at = DATETIME('now', 'localtime') WHERE rowid == NEW.rowid;
            END;

-- First Chatroom

INSERT INTO ChatRoom
(id, name, prompt, created_at, updated_at)
VALUES(0, 'Bot', '', DATETIME('now', 'localtime'), DATETIME('now', 'localtime'));

-- Create Index
CREATE INDEX idx_chatroom_id ON ChatRoom(id);
CREATE INDEX idx_message_id ON Message(id);
CREATE INDEX idx_code_id ON Code(id);