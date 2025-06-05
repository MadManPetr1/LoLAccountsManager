**LoL Accounts Manager**

A desktop application for managing multiple League of Legends accounts in a clean, hierarchical interface. Stores all data in a local SQLite database and provides seamless import/export, asynchronous data loading, and Riot API synchronization.

---

## Features

* **Hierarchical Tree View**
  Accounts are grouped by **Region** (All regions) and then by **Type** (“Mine” vs. “Others”). Expand/collapse nodes to focus on a particular subset.

* **Create / Read / Update / Delete (CRUD)**

  * **Create**: Click the “Add” button (or press Ctrl + N) to open a dialog and enter all account fields: Region, Type, Login, Password, Email and Riot ID.
  * **Read**: The tree view shows all stored accounts, nested under their Region and Type.
  * **Update**: Double-click any editable cell (Login, Password, Mail, Riot ID) to edit in place. Changes are immediately written back to the SQLite database. The “Password” column displays as `***`, but you can double-click to reveal and copy/edit.
  * **Delete**: Right-click any individual account row → choose “Delete” from the context menu to remove that account. A “Delete Database” toolbar button will wipe all records and recreate an empty database.

* **Password Handling**

  * Stored passwords are masked as `***` in the table.

* **Asynchronous Database I/O**

  * Initial load (and subsequent reloads after imports) are performed in a background thread so the UI remains responsive.

* **Import / Export**

  * **CSV**

    * Automatically detects encoding (UTF-8 with BOM, UTF-8, CP1250 (ISO 8859-2), Latin-1) to support special characters (e.g. Š/ě).
    * Optionally previews the first 10 rows in a dialog before committing the data to the database.
  * **JSON**

    * Round-trip serialization of all fields.

* **Riot API Synchronization (TO_DO)**
    
  * “Sync Riot” toolbar button fetches each account’s latest Level and Ranked Solo/Duo wins & losses from Riot’s API.
  * Uses the stored **Riot ID** (`GameName#TagLine`) to first obtain PUUID (via the Account-V1 endpoint on `europe.api.riotgames.com`), then Summoner-V4 to get `summonerLevel` and encrypted Summoner ID, then League-V4 to find the “RANKED\_SOLO\_5x5” entry.
  * Updates Level, Wins, Losses, and recalculates Win Rate.
  * Requires a valid (non-expired) Riot Developer API key.

* **Dynamic Column Sizing & Centered Text**

  * Columns auto-resize to fit either the header label or the largest cell in that column.
  * All text is centered.

* **Persistent UI State**

  * Saves and restores window size & position, column widths, and expanded/collapsed state of each Region/Type node.

* **High-DPI Support**

  * Calls `QGuiApplication.setHighDpiScaleFactorRoundingPolicy(Qt.HighDpiScaleFactorRoundingPolicy.PassThrough)` before creating the QApplication to ensure crisp scaling on modern displays.

* **Daily Backup**

  * Each time the app launches (or the close event fires), it writes out the full database as `exports/<today>.csv` (e.g. `exports/05-06-2025.csv`).