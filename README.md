# LoLAccountsManager
**LoLAccountsManager** is a robust, windows desktop application designed to make juggling multiple League of Legends accounts effortless, secure, and visually intuitive. Below is an in-depth look at every facet of the app—from the user experience and core workflows to the underlying architecture, data management, and security mechanisms.

## 1. User Experience & Workflows
### 1.1. Main Window Layout
1. **Sidebar Tree View**
   * **Region Nodes**: Populated dynamically from Riot’s supported regions.
   * **Type Sub-Nodes**: Under each region, two default types: “Mine” and “Others”.
   * **Sorting**: Live-sorting by Level under each sub-node.

2. **Toolbar & Shortcuts**
   * **Add Account (Ctrl + N)**: Opens a modal dialog for entering Region, Type, Username, Password, Email, and Riot ID. All fields validate on submit.
   * **Import/Export**: Buttons open file pickers for CSV or JSON. Encoding is auto-detected (UTF-8 BOM, UTF-8, CP1250, Latin-1).
   * **Delete Database**: Wipes all data after confirmation.

3. **Main Panel – Data Grid**
   * **Columns**: Region, Type, Username, Password (masked as `***`), Level, Email, Ranked, Wins/Losses, Winrate (%), Riot ID.
   * **Dynamic Sizing & Centering**: Columns auto-resize to fit the largest content and header; all text is horizontally centered.
   * **Inline Editing**: Double-click any cell (except Winrate) to edit. Editing the Password cell temporarily reveals the plaintext and lets you change or copy it. Changes write back immediately to SQLite.
   * **Context Menu**: Right-click a row to Copy Password or Delete the Account.

4. **Status & Logs Panel**
   * Shows background task progress: database loads, import/export, Riot API sync.
   * Error messages with “Retry” and “Details” links.

## 2. Core Features & Extensions
### 2.1. Hierarchical Organization
* By "Region" as a parent and then “Mine”/“Others" as children and then each account row. (expandable and collapsable)

### 2.2. Import/Export & Backups
* **Import**: Validates each row, reports malformed entries, and skips duplicates (by region + username).
* **Manual Export**: Save as CSV or JSON.
* **Daily Backup**: On every launch and exit, the app exports the entire database to `exports/YYYY-MM-DD.csv`. If a file for today already exists, it’s overwritten.

### 2.3. Riot API Synchronization
* **Level, Rank in Solo/Duo and Wins/losses in Solo/Duo**: In Settings you link your Riot API key; then manually, the app fetches each account’s levels, current rank, and win/loss ratios in solo/duo.

## 3. Technical Architecture
### 3.1. Layered Design
1. **UI Layer**:
   * **PySide6, Python** implementing all visual components, keyboard shortcuts, and theming.
2. **Service Layer**:
   * **Database Service**: Asynchronous wrapper around SQLite with connection pooling; publishes events to the UI via an event bus.
   * **Import/Export Service**: CSV/JSON, auto-detect encoding, validate, and map fields.

## 4. Security & Data Integrity
* **Secure Delete**: When you delete an account or the entire database, records are securely overwritten before removal.
* **Backup Integrity**: CSV backups are checksummed; the app warns if a backup fails CRC validation.