/**
 * toolkit_capture.gs — Google Apps Script to capture toolkit downloads into a Google Sheet.
 *
 * ONE-TIME SETUP (about 3 minutes, all in your Google account):
 *   1. Create a new Google Sheet (e.g. "IIM Toolkit Leads"). Copy its ID from the URL:
 *        https://docs.google.com/spreadsheets/d/THIS_IS_THE_ID/edit
 *   2. Go to script.google.com -> New project. Paste this whole file in. Replace SHEET_ID below.
 *   3. Deploy -> New deployment -> type "Web app".
 *        Execute as: Me.   Who has access: Anyone.
 *      Click Deploy, authorise, and copy the Web app URL (ends in /exec).
 *   4. Paste that /exec URL into assets/gate.js as ENDPOINT, commit, push.
 *
 * That's it. Every gated download appends a row: timestamp, name, email, city, resource, type.
 */
var SHEET_ID = "PASTE_YOUR_GOOGLE_SHEET_ID_HERE";
var SHEET_NAME = "Leads";

function doPost(e) {
  try {
    var ss = SpreadsheetApp.openById(SHEET_ID);
    var sh = ss.getSheetByName(SHEET_NAME) || ss.insertSheet(SHEET_NAME);
    if (sh.getLastRow() === 0) {
      sh.appendRow(["Timestamp", "Name", "Email", "City", "Resource", "Type"]);
    }
    var p = (e && e.parameter) || {};
    sh.appendRow([new Date(), p.name || "", p.email || "", p.city || "", p.resource || "", p.type || ""]);
    return ContentService.createTextOutput(JSON.stringify({ ok: true }))
      .setMimeType(ContentService.MimeType.JSON);
  } catch (err) {
    return ContentService.createTextOutput(JSON.stringify({ ok: false, error: String(err) }))
      .setMimeType(ContentService.MimeType.JSON);
  }
}

function doGet() {
  return ContentService.createTextOutput("IIM toolkit capture is live.");
}
