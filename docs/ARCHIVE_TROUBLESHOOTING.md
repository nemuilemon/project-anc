# Archive Function Troubleshooting Guide

## ✅ Archive Function Status

The archive functionality has been **implemented and tested successfully**. All core components are working:

- ✅ **Archive Logic**: Files can be moved to `.archive` directory
- ✅ **Database Updates**: File status correctly updated to 'archived'
- ✅ **Unarchive Logic**: Files can be restored from archive
- ✅ **UI Integration**: Archive buttons and menus are connected
- ✅ **Error Handling**: **NEW** AlertDialog popups for clear error messages
- ✅ **Duplicate Detection**: **NEW** Specific warnings for same-name conflicts

## 🔧 How to Archive Files

### Method 1: Right-Click Context Menu
1. **Right-click** on any file in the file list
2. Select **"Archive file"** from the context menu
3. File will be moved to archive and disappear from active list

### Method 2: Popup Menu Button
1. Click the **⋮ (three dots)** button next to any file
2. Select **"Archive file"** from the dropdown menu
3. File will be archived and removed from view

### Method 3: Archive Explorer
1. Click **"Archive Explorer"** button in sidebar
2. View all archived files in the modal
3. Use **Unarchive**, **Open**, or **Delete** options

## 🐛 Common Issues and Solutions

### Issue 1: "Archive button not working"
**Possible Causes:**
- Right-click not detected (use `on_secondary_tap`)
- Menu button not visible
- Event handler not connected

**Solutions:**
- Try using the popup menu (⋮) instead of right-click
- Check console for debug messages
- Restart application

### Issue 2: "File not found error"
**Possible Causes:**
- File was moved or deleted externally
- Database out of sync with filesystem

**Solutions:**
- Refresh file list (restart app)
- Check if file exists in filesystem
- Run database sync

### Issue 3: "Same filename exists in archive" ⚠️ **NEW: POPUP DIALOG**
**Possible Causes:**
- A file with the same name already exists in archive folder

**New Error Handling:**
- **Alert Dialog**: Clear popup notification with specific filename
- **Detailed Message**: Explains exactly which file conflicts
- **Solution Guidance**: Suggests renaming before archiving

**Solutions:**
- Rename one of the files first using the "Rename file" option
- Check `.archive` folder manually to see conflicting file
- Use different filename to avoid conflict

### Issue 4: "Permission denied"
**Possible Causes:**
- File is open in another application
- Insufficient filesystem permissions
- File is read-only

**Solutions:**
- Close file in other applications
- Check file permissions
- Run as administrator (Windows)

## 🔍 Debug Information

### Debug Logs Enabled
The following debug messages are now logged to console:

```
Archive intent clicked for: [filename]
Handle archive intent for: [filename] at path: [filepath]
Handler: archive_file called with path: [filepath]
Archive operation started for: [filepath]
Archive path: [archive_path]
Moving file from [source] to [destination]
Database update result: [update_count]
```

### Manual Testing
You can test archive functionality directly:

```bash
python test_archive_function.py
```

This will test archive/unarchive operations independently of the UI.

## 📁 File Structure

```
data/
├── notes/              # Active files shown in main list
│   ├── .archive/       # Archived files (hidden from main list)
│   ├── file1.md
│   └── file2.md
└── anc_db.json        # Database with file metadata
```

## ⚡ Quick Fixes

### If Archive Function Completely Broken:

1. **Check Debug Console**
   ```bash
   python main.py
   # Look for error messages in console
   ```

2. **Test Archive Logic Directly**
   ```bash
   python test_archive_function.py
   ```

3. **Manual Archive (Emergency)**
   ```bash
   # Manually move file to archive
   mv "data/notes/filename.md" "data/notes/.archive/"

   # Update database status manually (requires database tools)
   ```

4. **Reset Archive Directory**
   ```bash
   # Remove all archived files (CAUTION: permanent)
   rm -rf data/notes/.archive/*
   ```

## 🎯 Expected Behavior

### Normal Archive Flow:
1. User clicks Archive option
2. Debug message: "Archive intent clicked"
3. Debug message: "Handle archive intent"
4. Debug message: "Handler: archive_file called"
5. Debug message: "Archive operation started"
6. File physically moved to `.archive/` folder
7. Database updated with new path and 'archived' status
8. File disappears from main file list
9. Success message displayed
10. File visible in Archive Explorer

### If Any Step Fails:
- Error message displayed to user
- File remains in original location
- Database unchanged
- Debug logs show where failure occurred

## 📞 Support

If archive function still doesn't work after trying these solutions:

1. **Check all debug messages** in console
2. **Run test script** to isolate UI vs logic issues
3. **Verify file permissions** and directory structure
4. **Check if files are locked** by other applications

The archive functionality is implemented correctly and tested - any issues are likely environmental or UI interaction related.