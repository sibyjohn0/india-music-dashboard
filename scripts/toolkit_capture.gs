/**
 * toolkit_capture.gs — Google Apps Script to capture toolkit downloads into a Google Sheet.
 * Field-agnostic: it writes whatever fields the form posts and auto-adds a column for any
 * new field, so changing the form never needs another redeploy.
 *
 * SETUP (once): new Google Sheet -> copy its ID into SHEET_ID below -> script.google.com,
 * paste this (SELECT ALL first, the editor auto-closes brackets) -> Deploy -> New deployment
 * -> Web app -> Execute as Me, Who has access Anyone -> Deploy -> copy the /exec URL into
 * assets/gate.js. To change the form later, just edit gate.js; no script change needed.
 */
var SHEET_ID = "PASTE_YOUR_GOOGLE_SHEET_ID_HERE";
var SHEET_NAME = "Leads";

function doPost(e) {
  var p = (e && e.parameter) || {};
  var ss = SpreadsheetApp.openById(SHEET_ID);
  var sh = ss.getSheetByName(SHEET_NAME) || ss.insertSheet(SHEET_NAME);
  var lastCol = sh.getLastColumn();
  var headers = (sh.getLastRow() > 0 && lastCol > 0) ? sh.getRange(1, 1, 1, lastCol).getValues()[0] : [];
  if (headers.length === 0) { headers = ["Timestamp"]; sh.getRange(1, 1).setValue("Timestamp"); }
  var keys = Object.keys(p);
  for (var i = 0; i < keys.length; i++) {
    if (headers.indexOf(keys[i]) === -1) { headers.push(keys[i]); sh.getRange(1, headers.length).setValue(keys[i]); }
  }
  var row = [];
  for (var j = 0; j < headers.length; j++) row.push("");
  row[0] = new Date();
  for (var k = 0; k < keys.length; k++) row[headers.indexOf(keys[k])] = p[keys[k]];
  sh.appendRow(row);
  return ContentService.createTextOutput("ok");
}

function doGet() {
  return ContentService.createTextOutput("IIM toolkit capture is live.");
}
