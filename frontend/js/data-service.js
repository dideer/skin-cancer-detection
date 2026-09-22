/**
 * data-service.js
 * ============================================================
 * DermisAI — Clinical Skin Cancer Detection System
 * Unified data access layer.
 *
 * USAGE:
 *   import { getPatients, createPrediction, ... } from './data-service.js'
 *   All functions return Promises and use the field shapes defined
 *   in the spec (Section 6). Pages must never call fetch() or
 *   reference local data arrays directly.
 *
 * TO CONNECT A REAL BACKEND:
 *   1. Set USE_DEMO_DATA = false
 *   2. Set API_BASE_URL to your API root
 *   That is the only change needed — no page code changes.
 * ============================================================
 */

const USE_DEMO_DATA = true;
const API_BASE_URL  = "http://localhost:3000/api";

/* ============================================================
   DEMO DATA
   ============================================================ */

const _USERS = [
  { name: "Dr. Sarah Okonkwo",    email: "s.okonkwo@cityhospital.org",  role: "dermatologist",       hospital: "City General Hospital",   status: "active",   last_login: "2026-09-15T08:42:00Z" },
  { name: "Dr. Marcus Reeves",    email: "m.reeves@cityhospital.org",   role: "general_practitioner", hospital: "City General Hospital",   status: "active",   last_login: "2026-09-14T16:10:00Z" },
  { name: "Nurse Chen Lijuan",    email: "c.lijuan@cityhospital.org",   role: "nurse",               hospital: "City General Hospital",   status: "active",   last_login: "2026-09-15T07:55:00Z" },
  { name: "Admin J. Hartwell",    email: "j.hartwell@cityhospital.org", role: "admin",               hospital: "City General Hospital",   status: "active",   last_login: "2026-09-13T09:00:00Z" },
  { name: "Dr. Priya Sharma",     email: "p.sharma@northmed.org",       role: "dermatologist",       hospital: "North Medical Centre",    status: "active",   last_login: "2026-09-15T10:20:00Z" },
  { name: "Dr. Tomás Ferreira",   email: "t.ferreira@northmed.org",     role: "general_practitioner", hospital: "North Medical Centre",   status: "inactive", last_login: "2026-08-28T14:00:00Z" },
  { name: "Nurse Amara Diallo",   email: "a.diallo@northmed.org",       role: "nurse",               hospital: "North Medical Centre",    status: "active",   last_login: "2026-09-14T11:30:00Z" },
  { name: "Dr. Ivan Sokolov",     email: "i.sokolov@eastclinic.org",    role: "dermatologist",       hospital: "East District Clinic",    status: "active",   last_login: "2026-09-12T09:15:00Z" },
  { name: "Admin Rosa Navarro",   email: "r.navarro@eastclinic.org",    role: "admin",               hospital: "East District Clinic",    status: "inactive", last_login: "2026-07-15T08:00:00Z" },
  { name: "Nurse Kim Jae-won",    email: "k.jaewon@eastclinic.org",     role: "nurse",               hospital: "East District Clinic",    status: "active",   last_login: "2026-09-15T06:45:00Z" },
];

const _HOSPITALS = [
  { name: "City General Hospital",   city: "London",    country: "United Kingdom", users: 4,  patients: 312, registered: "2025-01-15" },
  { name: "North Medical Centre",    city: "Manchester", country: "United Kingdom", users: 3, patients: 189, registered: "2025-03-08" },
  { name: "East District Clinic",    city: "Birmingham", country: "United Kingdom", users: 3, patients: 97,  registered: "2025-06-22" },
  { name: "St. Annes Dermatology",   city: "Bristol",   country: "United Kingdom", users: 2,  patients: 54,  registered: "2025-08-10" },
  { name: "Royal Skin Institute",    city: "Edinburgh", country: "United Kingdom", users: 5,  patients: 421, registered: "2024-11-01" },
];

const _PATIENTS = [
  { id: "PAT-0001", age_group: "55–64",  skin_type: "III", predictions: 3, last_seen: "2026-09-14", status: "active" },
  { id: "PAT-0002", age_group: "35–44",  skin_type: "II",  predictions: 1, last_seen: "2026-09-13", status: "active" },
  { id: "PAT-0003", age_group: "65–74",  skin_type: "IV",  predictions: 5, last_seen: "2026-09-11", status: "flagged" },
  { id: "PAT-0004", age_group: "25–34",  skin_type: "I",   predictions: 1, last_seen: "2026-09-10", status: "active" },
  { id: "PAT-0005", age_group: "45–54",  skin_type: "V",   predictions: 2, last_seen: "2026-09-09", status: "active" },
  { id: "PAT-0006", age_group: "75+",    skin_type: "II",  predictions: 4, last_seen: "2026-09-08", status: "flagged" },
  { id: "PAT-0007", age_group: "18–24",  skin_type: "I",   predictions: 1, last_seen: "2026-09-07", status: "active" },
  { id: "PAT-0008", age_group: "55–64",  skin_type: "VI",  predictions: 2, last_seen: "2026-09-06", status: "active" },
  { id: "PAT-0009", age_group: "45–54",  skin_type: "III", predictions: 3, last_seen: "2026-09-05", status: "active" },
  { id: "PAT-0010", age_group: "65–74",  skin_type: "II",  predictions: 6, last_seen: "2026-09-04", status: "flagged" },
  { id: "PAT-0011", age_group: "35–44",  skin_type: "IV",  predictions: 1, last_seen: "2026-09-03", status: "active" },
  { id: "PAT-0012", age_group: "25–34",  skin_type: "V",   predictions: 2, last_seen: "2026-09-02", status: "active" },
];

const _PREDICTIONS = [
  { id: "PRED-1091", patient: "PAT-0001", clinician: "Dr. Sarah Okonkwo",  result: "cancer_detected", probability: 0.87, referral: true,  location: "Left forearm",    verified: true,  time: "2026-09-14T14:32:00Z", status: "reviewed" },
  { id: "PRED-1090", patient: "PAT-0002", clinician: "Dr. Marcus Reeves",  result: "healthy",         probability: 0.12, referral: false, location: "Upper back",      verified: true,  time: "2026-09-13T11:15:00Z", status: "reviewed" },
  { id: "PRED-1089", patient: "PAT-0003", clinician: "Dr. Sarah Okonkwo",  result: "cancer_detected", probability: 0.93, referral: true,  location: "Right shoulder",  verified: false, time: "2026-09-11T09:50:00Z", status: "pending" },
  { id: "PRED-1088", patient: "PAT-0004", clinician: "Dr. Priya Sharma",   result: "healthy",         probability: 0.07, referral: false, location: "Left calf",       verified: true,  time: "2026-09-10T15:20:00Z", status: "reviewed" },
  { id: "PRED-1087", patient: "PAT-0005", clinician: "Dr. Marcus Reeves",  result: "healthy",         probability: 0.19, referral: false, location: "Neck",            verified: true,  time: "2026-09-09T10:05:00Z", status: "reviewed" },
  { id: "PRED-1086", patient: "PAT-0006", clinician: "Dr. Sarah Okonkwo",  result: "cancer_detected", probability: 0.78, referral: true,  location: "Right hand",      verified: false, time: "2026-09-08T13:40:00Z", status: "pending" },
  { id: "PRED-1085", patient: "PAT-0007", clinician: "Dr. Ivan Sokolov",   result: "healthy",         probability: 0.04, referral: false, location: "Left temple",     verified: true,  time: "2026-09-07T08:30:00Z", status: "reviewed" },
  { id: "PRED-1084", patient: "PAT-0008", clinician: "Dr. Priya Sharma",   result: "healthy",         probability: 0.22, referral: false, location: "Upper chest",     verified: true,  time: "2026-09-06T12:10:00Z", status: "reviewed" },
  { id: "PRED-1083", patient: "PAT-0009", clinician: "Dr. Sarah Okonkwo",  result: "cancer_detected", probability: 0.65, referral: true,  location: "Lower back",      verified: false, time: "2026-09-05T16:25:00Z", status: "pending" },
  { id: "PRED-1082", patient: "PAT-0010", clinician: "Dr. Marcus Reeves",  result: "cancer_detected", probability: 0.91, referral: true,  location: "Scalp",           verified: true,  time: "2026-09-04T09:55:00Z", status: "reviewed" },
];

const _AUDIT_LOGS = [
  { id: "LOG-8821", user: "Dr. Sarah Okonkwo",  action: "CREATE_PREDICTION",  table: "predictions", time: "2026-09-15T08:44:12Z", ip: "10.0.1.42",  status: "success" },
  { id: "LOG-8820", user: "Admin J. Hartwell",  action: "CREATE_USER",        table: "users",       time: "2026-09-15T08:30:05Z", ip: "10.0.1.10",  status: "success" },
  { id: "LOG-8819", user: "Nurse Chen Lijuan",  action: "VIEW_PATIENT",       table: "patients",    time: "2026-09-15T07:58:41Z", ip: "10.0.1.88",  status: "success" },
  { id: "LOG-8818", user: "Dr. Marcus Reeves",  action: "VERIFY_PREDICTION",  table: "predictions", time: "2026-09-14T16:12:30Z", ip: "10.0.1.55",  status: "success" },
  { id: "LOG-8817", user: "Dr. Priya Sharma",   action: "CREATE_PATIENT",     table: "patients",    time: "2026-09-14T15:40:22Z", ip: "192.168.2.7", status: "success" },
  { id: "LOG-8816", user: "system",             action: "SCHEDULED_BACKUP",   table: "system",      time: "2026-09-14T12:00:00Z", ip: "127.0.0.1",  status: "success" },
  { id: "LOG-8815", user: "Admin Rosa Navarro", action: "LOGIN",              table: "sessions",    time: "2026-09-14T09:05:11Z", ip: "10.0.2.15",  status: "failed"  },
  { id: "LOG-8814", user: "Dr. Sarah Okonkwo",  action: "CREATE_PREDICTION",  table: "predictions", time: "2026-09-13T14:28:09Z", ip: "10.0.1.42",  status: "success" },
  { id: "LOG-8813", user: "Admin J. Hartwell",  action: "UPDATE_HOSPITAL",    table: "hospitals",   time: "2026-09-13T11:15:55Z", ip: "10.0.1.10",  status: "success" },
  { id: "LOG-8812", user: "Nurse Amara Diallo", action: "VIEW_PATIENT",       table: "patients",    time: "2026-09-13T10:44:02Z", ip: "192.168.2.9", status: "success" },
  { id: "LOG-8811", user: "Dr. Ivan Sokolov",   action: "CREATE_PREDICTION",  table: "predictions", time: "2026-09-13T09:20:18Z", ip: "10.0.3.22",  status: "success" },
  { id: "LOG-8810", user: "Dr. Marcus Reeves",  action: "LOGIN",              table: "sessions",    time: "2026-09-13T08:58:47Z", ip: "10.0.1.55",  status: "success" },
  { id: "LOG-8809", user: "system",             action: "INTEGRITY_CHECK",    table: "system",      time: "2026-09-13T06:00:00Z", ip: "127.0.0.1",  status: "success" },
  { id: "LOG-8808", user: "Nurse Kim Jae-won",  action: "VIEW_AUDIT_LOG",     table: "audit_logs",  time: "2026-09-12T17:10:33Z", ip: "10.0.3.80",  status: "failed"  },
  { id: "LOG-8807", user: "Dr. Sarah Okonkwo",  action: "VERIFY_PREDICTION",  table: "predictions", time: "2026-09-12T15:55:14Z", ip: "10.0.1.42",  status: "success" },
  { id: "LOG-8806", user: "Admin J. Hartwell",  action: "DEACTIVATE_USER",    table: "users",       time: "2026-09-12T14:02:08Z", ip: "10.0.1.10",  status: "success" },
  { id: "LOG-8805", user: "Dr. Priya Sharma",   action: "CREATE_PREDICTION",  table: "predictions", time: "2026-09-11T11:38:29Z", ip: "192.168.2.7", status: "success" },
  { id: "LOG-8804", user: "Dr. Ivan Sokolov",   action: "LOGIN",              table: "sessions",    time: "2026-09-11T09:10:55Z", ip: "10.0.3.22",  status: "success" },
];

const _CURRENT_USER = _USERS[0]; // Dr. Sarah Okonkwo

/* helpers */
function _delay(ms = 400) {
  return new Promise(resolve => setTimeout(resolve, ms));
}

function _paginate(arr, page = 1, perPage = 10) {
  const start = (page - 1) * perPage;
  return {
    items: arr.slice(start, start + perPage),
    total: arr.length,
    page,
    perPage,
    totalPages: Math.ceil(arr.length / perPage),
  };
}

/* ============================================================
   PUBLIC API — DEMO IMPLEMENTATIONS
   ============================================================ */

async function _demoCurrentUser() {
  await _delay(300);
  return { ..._CURRENT_USER };
}

async function _demoLogin(email, password) {
  await _delay(700);
  const user = _USERS.find(u => u.email === email);
  if (!user || password.length < 4) {
    throw new Error("Invalid email or password.");
  }
  return { token: "demo-token-abc123", user: { ...user } };
}

async function _demoDashboardStats() {
  await _delay(450);
  return {
    predictions_this_week: 47,
    referrals_flagged:     12,
    avg_processing_ms:     1840,
    active_clinicians:     8,
    delta_predictions:     "+14%",
    delta_referrals:       "+3",
    delta_processing:      "-120ms",
    delta_clinicians:      "+1",
    weekly_chart: [
      { label: "Mon", predictions: 9,  referrals: 2 },
      { label: "Tue", predictions: 12, referrals: 4 },
      { label: "Wed", predictions: 6,  referrals: 1 },
      { label: "Thu", predictions: 8,  referrals: 3 },
      { label: "Fri", predictions: 7,  referrals: 1 },
      { label: "Sat", predictions: 3,  referrals: 1 },
      { label: "Sun", predictions: 2,  referrals: 0 },
    ],
    result_distribution: { cancer_detected: 12, healthy: 35 },
  };
}

async function _demoRecentPredictions(limit = 5) {
  await _delay(350);
  return _PREDICTIONS.slice(0, limit).map(p => ({ ...p }));
}

async function _demoGetPatients({ search = "", skin_type = "", status = "", page = 1, perPage = 10 } = {}) {
  await _delay(380);
  let filtered = [..._PATIENTS];
  if (search)    filtered = filtered.filter(p => p.id.toLowerCase().includes(search.toLowerCase()));
  if (skin_type) filtered = filtered.filter(p => p.skin_type === skin_type);
  if (status)    filtered = filtered.filter(p => p.status === status);
  return _paginate(filtered, page, perPage);
}

async function _demoGetUsers({ search = "", role = "", status = "", hospital = "", page = 1, perPage = 10 } = {}) {
  await _delay(360);
  let filtered = [..._USERS];
  if (search)   filtered = filtered.filter(u => u.name.toLowerCase().includes(search.toLowerCase()) || u.email.toLowerCase().includes(search.toLowerCase()));
  if (role)     filtered = filtered.filter(u => u.role === role);
  if (status)   filtered = filtered.filter(u => u.status === status);
  if (hospital) filtered = filtered.filter(u => u.hospital === hospital);
  return _paginate(filtered, page, perPage);
}

async function _demoGetHospitals({ search = "", page = 1, perPage = 10 } = {}) {
  await _delay(330);
  let filtered = [..._HOSPITALS];
  if (search) filtered = filtered.filter(h => h.name.toLowerCase().includes(search.toLowerCase()) || h.city.toLowerCase().includes(search.toLowerCase()));
  return _paginate(filtered, page, perPage);
}

async function _demoGetAuditLogs({ search = "", action = "", status = "", page = 1, perPage = 15 } = {}) {
  await _delay(400);
  let filtered = [..._AUDIT_LOGS];
  if (search) filtered = filtered.filter(l =>
    l.user.toLowerCase().includes(search.toLowerCase()) ||
    l.action.toLowerCase().includes(search.toLowerCase()) ||
    l.id.toLowerCase().includes(search.toLowerCase())
  );
  if (action) filtered = filtered.filter(l => l.action === action);
  if (status) filtered = filtered.filter(l => l.status === status);
  return _paginate(filtered, page, perPage);
}

async function _demoCreatePrediction(payload) {
  await _delay(1800); // simulate model inference time
  const isCancer = Math.random() > 0.55;
  const probability = isCancer
    ? 0.60 + Math.random() * 0.38
    : 0.03 + Math.random() * 0.30;
  const newPred = {
    id:          `PRED-${1092 + _PREDICTIONS.length}`,
    patient:     payload.patient_id,
    clinician:   _CURRENT_USER.name,
    result:      isCancer ? "cancer_detected" : "healthy",
    probability: parseFloat(probability.toFixed(3)),
    referral:    isCancer && probability > 0.70,
    location:    payload.location || "Unspecified",
    verified:    false,
    time:        new Date().toISOString(),
    status:      "pending",
    processing_ms: 1800 + Math.floor(Math.random() * 400),
    confidence:  parseFloat((0.80 + Math.random() * 0.18).toFixed(2)),
    image_path:  `/storage/images/demo/${payload.patient_id}/${Date.now()}.jpg`,
  };
  _PREDICTIONS.unshift(newPred);
  return newPred;
}

async function _demoRegisterPatient(payload) {
  await _delay(500);
  const newPatient = {
    id:          `PAT-${String(_PATIENTS.length + 1).padStart(4, "0")}`,
    age_group:   payload.age_group,
    skin_type:   payload.skin_type,
    predictions: 0,
    last_seen:   new Date().toISOString().split("T")[0],
    status:      "active",
  };
  _PATIENTS.unshift(newPatient);
  return newPatient;
}

async function _demoVerifyPrediction(predId, clinicianVerdict) {
  await _delay(400);
  const pred = _PREDICTIONS.find(p => p.id === predId);
  if (!pred) throw new Error("Prediction not found.");
  pred.verified = true;
  pred.status   = "reviewed";
  pred.clinician_verdict = clinicianVerdict;
  return { ...pred };
}

/* ============================================================
   PUBLIC API — REAL FETCH IMPLEMENTATIONS (used when USE_DEMO_DATA = false)
   ============================================================ */

async function _fetchCurrentUser() {
  const res = await fetch(`${API_BASE_URL}/auth/me`, { credentials: "include" });
  if (!res.ok) throw new Error("Failed to load user profile.");
  return res.json();
}

async function _fetchLogin(email, password) {
  const res = await fetch(`${API_BASE_URL}/auth/login`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ email, password }),
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({}));
    throw new Error(err.message || "Login failed.");
  }
  return res.json();
}

async function _fetchDashboardStats() {
  const res = await fetch(`${API_BASE_URL}/dashboard/stats`, { credentials: "include" });
  if (!res.ok) throw new Error("Failed to load dashboard stats.");
  return res.json();
}

async function _fetchRecentPredictions(limit = 5) {
  const res = await fetch(`${API_BASE_URL}/predictions?limit=${limit}`, { credentials: "include" });
  if (!res.ok) throw new Error("Failed to load recent predictions.");
  return res.json();
}

async function _fetchGetPatients(filters = {}) {
  const params = new URLSearchParams(filters);
  const res = await fetch(`${API_BASE_URL}/patients?${params}`, { credentials: "include" });
  if (!res.ok) throw new Error("Failed to load patients.");
  return res.json();
}

async function _fetchGetUsers(filters = {}) {
  const params = new URLSearchParams(filters);
  const res = await fetch(`${API_BASE_URL}/users?${params}`, { credentials: "include" });
  if (!res.ok) throw new Error("Failed to load users.");
  return res.json();
}

async function _fetchGetHospitals(filters = {}) {
  const params = new URLSearchParams(filters);
  const res = await fetch(`${API_BASE_URL}/hospitals?${params}`, { credentials: "include" });
  if (!res.ok) throw new Error("Failed to load hospitals.");
  return res.json();
}

async function _fetchGetAuditLogs(filters = {}) {
  const params = new URLSearchParams(filters);
  const res = await fetch(`${API_BASE_URL}/audit-logs?${params}`, { credentials: "include" });
  if (!res.ok) throw new Error("Failed to load audit logs.");
  return res.json();
}

async function _fetchCreatePrediction(payload) {
  const formData = new FormData();
  Object.entries(payload).forEach(([k, v]) => formData.append(k, v));
  const res = await fetch(`${API_BASE_URL}/predictions`, {
    method: "POST",
    credentials: "include",
    body: formData,
  });
  if (!res.ok) throw new Error("Prediction failed. Please try again.");
  return res.json();
}

async function _fetchRegisterPatient(payload) {
  const res = await fetch(`${API_BASE_URL}/patients`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    credentials: "include",
    body: JSON.stringify(payload),
  });
  if (!res.ok) throw new Error("Failed to register patient.");
  return res.json();
}

async function _fetchVerifyPrediction(predId, clinicianVerdict) {
  const res = await fetch(`${API_BASE_URL}/predictions/${predId}/verify`, {
    method: "PATCH",
    headers: { "Content-Type": "application/json" },
    credentials: "include",
    body: JSON.stringify({ verdict: clinicianVerdict }),
  });
  if (!res.ok) throw new Error("Failed to submit verification.");
  return res.json();
}

/* ============================================================
   EXPORTED PUBLIC FUNCTIONS
   Each function routes to demo or real fetch based on the flag.
   ============================================================ */

export function getCurrentUser() {
  return USE_DEMO_DATA ? _demoCurrentUser() : _fetchCurrentUser();
}

export function login(email, password) {
  return USE_DEMO_DATA ? _demoLogin(email, password) : _fetchLogin(email, password);
}

export function getDashboardStats() {
  return USE_DEMO_DATA ? _demoDashboardStats() : _fetchDashboardStats();
}

export function getRecentPredictions(limit = 5) {
  return USE_DEMO_DATA ? _demoRecentPredictions(limit) : _fetchRecentPredictions(limit);
}

export function getPatients(filters = {}) {
  return USE_DEMO_DATA ? _demoGetPatients(filters) : _fetchGetPatients(filters);
}

export function getUsers(filters = {}) {
  return USE_DEMO_DATA ? _demoGetUsers(filters) : _fetchGetUsers(filters);
}

export function getHospitals(filters = {}) {
  return USE_DEMO_DATA ? _demoGetHospitals(filters) : _fetchGetHospitals(filters);
}

export function getAuditLogs(filters = {}) {
  return USE_DEMO_DATA ? _demoGetAuditLogs(filters) : _fetchGetAuditLogs(filters);
}

export function createPrediction(payload) {
  return USE_DEMO_DATA ? _demoCreatePrediction(payload) : _fetchCreatePrediction(payload);
}

export function registerPatient(payload) {
  return USE_DEMO_DATA ? _demoRegisterPatient(payload) : _fetchRegisterPatient(payload);
}

export function verifyPrediction(predId, clinicianVerdict) {
  return USE_DEMO_DATA ? _demoVerifyPrediction(predId, clinicianVerdict) : _fetchVerifyPrediction(predId, clinicianVerdict);
}

/* convenience re-export of demo patient list for dropdowns (pages never access _PATIENTS directly) */
export function getPatientList() {
  return USE_DEMO_DATA
    ? Promise.resolve([..._PATIENTS].map(p => ({ id: p.id, age_group: p.age_group, skin_type: p.skin_type })))
    : fetch(`${API_BASE_URL}/patients?perPage=200`, { credentials: "include" }).then(r => r.json()).then(d => d.items);
}
