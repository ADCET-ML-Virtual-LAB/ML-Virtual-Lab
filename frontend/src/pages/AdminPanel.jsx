import { useState, useEffect } from "react";
import { batchesApi } from "../api/batches.js";
import { authApi } from "../api/auth.js";
import { experimentsApi } from "../api/experiments.js";
import "./AdminPanel.css";

const TABS = [
  { id: "batches", label: "Batches & Students" },
  { id: "instructors", label: "Instructors" },
  { id: "experiments", label: "Experiments" },
];

export default function AdminPanel() {
  const [activeTab, setActiveTab] = useState("batches");

  return (
    <div className="admin-panel">
      <div className="admin-panel__header">
        <h1 className="admin-panel__title">Admin Panel</h1>
      </div>

      <nav className="exp-page__tabs">
        {TABS.map((t) => (
          <button
            key={t.id}
            className={`exp-tab ${activeTab === t.id ? "exp-tab--active" : ""}`}
            onClick={() => setActiveTab(t.id)}
          >
            {t.label}
          </button>
        ))}
      </nav>

      <div className="admin-panel__content">
        {activeTab === "batches" && <BatchesTab />}
        {activeTab === "instructors" && <InstructorsTab />}
        {activeTab === "experiments" && <ExperimentsTab />}
      </div>
    </div>
  );
}

// ── Batches Tab ─────────────────────────────────────────────────────────────

function BatchesTab() {
  const [batches, setBatches] = useState([]);
  const [users, setUsers] = useState([]);
  const [selectedBatch, setSelectedBatch] = useState("");
  
  // Create Batch State
  const [name, setName] = useState("");
  const [academicYear, setAcademicYear] = useState("");
  
  // Upload Roster State
  const [rosterCsv, setRosterCsv] = useState("");
  
  // Assign Instructor State
  const [selectedInstructor, setSelectedInstructor] = useState("");

  const [message, setMessage] = useState("");
  const [error, setError] = useState("");

  useEffect(() => {
    loadData();
  }, []);

  async function loadData() {
    try {
      const [b, u] = await Promise.all([batchesApi.list(), authApi.listUsers()]);
      setBatches(b);
      setUsers(u.filter((user) => user.role === "instructor"));
      if (b.length > 0) setSelectedBatch(b[0].id);
    } catch (err) {
      setError("Failed to load initial data.");
    }
  }

  async function handleCreateBatch(e) {
    e.preventDefault();
    setMessage(""); setError("");
    try {
      await batchesApi.create(name, academicYear);
      setMessage("Batch created successfully.");
      setName(""); setAcademicYear("");
      loadData();
    } catch (err) {
      setError(err.response?.data?.detail || "Failed to create batch");
    }
  }

  async function handleUploadRoster(e) {
    e.preventDefault();
    setMessage(""); setError("");
    if (!selectedBatch) return setError("Select a batch first.");
    
    // Naive CSV parse
    const lines = rosterCsv.split("\n").map(l => l.trim()).filter(l => l);
    const students = lines.map(line => {
      const [email, full_name, roll_number] = line.split(",").map(s => s.trim());
      return { email, full_name, roll_number: roll_number || null };
    });

    try {
      const res = await batchesApi.uploadStudents(selectedBatch, students);
      setMessage(`Uploaded! Created: ${res.created}, Skipped/Existing: ${res.skipped}`);
      setRosterCsv("");
    } catch (err) {
      setError(err.response?.data?.detail || "Failed to upload students");
    }
  }

  async function handleAssignInstructor(e) {
    e.preventDefault();
    setMessage(""); setError("");
    if (!selectedBatch || !selectedInstructor) return setError("Select both batch and instructor.");
    try {
      await batchesApi.assignInstructor(selectedBatch, selectedInstructor);
      setMessage("Instructor assigned successfully.");
    } catch (err) {
      setError(err.response?.data?.detail || "Failed to assign instructor");
    }
  }

  return (
    <div className="admin-tab">
      {message && <div className="alert alert--success">{message}</div>}
      {error && <div className="alert alert--error">{error}</div>}

      <div className="admin-grid">
        <div className="card">
          <h2 className="section-header">Create Batch</h2>
          <form onSubmit={handleCreateBatch} className="auth-form">
            <label className="form-label">
              Name (e.g. TE-CSE-A)
              <input className="form-input" value={name} onChange={e => setName(e.target.value)} required />
            </label>
            <label className="form-label">
              Academic Year (e.g. 2026-27)
              <input className="form-input" value={academicYear} onChange={e => setAcademicYear(e.target.value)} required />
            </label>
            <button className="btn btn--primary">Create Batch</button>
          </form>
        </div>

        <div className="card">
          <h2 className="section-header">Manage Existing Batch</h2>
          <label className="form-label mb-2">
            Select Batch:
            <select className="form-select" value={selectedBatch} onChange={e => setSelectedBatch(e.target.value)}>
              {batches.map(b => <option key={b.id} value={b.id}>{b.name} ({b.academic_year})</option>)}
            </select>
          </label>

          <hr className="admin-divider" />
          
          <h3 className="section-header" style={{fontSize: '1rem'}}>Upload Roster</h3>
          <p className="admin-help">Format: email, Full Name, RollNumber (one per line)</p>
          <form onSubmit={handleUploadRoster} className="auth-form">
            <textarea 
              className="form-textarea" 
              value={rosterCsv} 
              onChange={e => setRosterCsv(e.target.value)}
              placeholder="student1@college.edu, Asha Patil, 21CS101"
              required
            />
            <button className="btn btn--ghost">Upload Students</button>
          </form>

          <hr className="admin-divider" />

          <h3 className="section-header" style={{fontSize: '1rem'}}>Assign Instructor</h3>
          <form onSubmit={handleAssignInstructor} className="auth-form">
            <select className="form-select" value={selectedInstructor} onChange={e => setSelectedInstructor(e.target.value)} required>
              <option value="">-- Select Instructor --</option>
              {users.map(u => <option key={u.id} value={u.id}>{u.full_name} ({u.email})</option>)}
            </select>
            <button className="btn btn--ghost">Assign</button>
          </form>
        </div>
      </div>
    </div>
  );
}

// ── Instructors Tab ─────────────────────────────────────────────────────────

function InstructorsTab() {
  const [instructors, setInstructors] = useState([]);
  const [fullName, setFullName] = useState("");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [message, setMessage] = useState("");
  const [error, setError] = useState("");

  useEffect(() => { loadInstructors(); }, []);

  async function loadInstructors() {
    try {
      const u = await authApi.listUsers();
      setInstructors(u.filter((user) => user.role === "instructor"));
    } catch (err) {
      setError("Failed to load instructors.");
    }
  }

  async function handleCreate(e) {
    e.preventDefault();
    setMessage(""); setError("");
    try {
      await authApi.createInstructor(fullName, email, password);
      setMessage("Instructor created.");
      setFullName(""); setEmail(""); setPassword("");
      loadInstructors();
    } catch (err) {
      setError(err.response?.data?.detail || "Creation failed");
    }
  }

  return (
    <div className="admin-tab admin-grid">
      <div className="card">
        <h2 className="section-header">Create Instructor</h2>
        {message && <div className="alert alert--success mb-2">{message}</div>}
        {error && <div className="alert alert--error mb-2">{error}</div>}
        
        <form onSubmit={handleCreate} className="auth-form">
          <label className="form-label">
            Full Name
            <input className="form-input" value={fullName} onChange={e => setFullName(e.target.value)} required />
          </label>
          <label className="form-label">
            Email
            <input type="email" className="form-input" value={email} onChange={e => setEmail(e.target.value)} required />
          </label>
          <label className="form-label">
            Initial Password
            <input type="password" className="form-input" value={password} onChange={e => setPassword(e.target.value)} required minLength={8}/>
          </label>
          <button className="btn btn--primary">Create Instructor</button>
        </form>
      </div>
      <div className="card">
        <h2 className="section-header">Existing Instructors</h2>
        <ul>
          {instructors.map(ins => (
            <li key={ins.id} className="mb-2">
              <strong>{ins.full_name}</strong> &lt;{ins.email}&gt;
            </li>
          ))}
          {instructors.length === 0 && <p className="admin-help">No instructors found.</p>}
        </ul>
      </div>
    </div>
  );
}

// ── Experiments Tab ─────────────────────────────────────────────────────────

function ExperimentsTab() {
  const [experiments, setExperiments] = useState([]);
  const [title, setTitle] = useState("");
  const [slug, setSlug] = useState("");
  const [aim, setAim] = useState("");
  const [objective, setObjective] = useState("");
  
  const [selectedExp, setSelectedExp] = useState(null);
  const [evalSpecJson, setEvalSpecJson] = useState("");
  
  const [message, setMessage] = useState("");
  const [error, setError] = useState("");

  useEffect(() => { loadExperiments(); }, []);

  async function loadExperiments() {
    try {
      const e = await experimentsApi.list();
      setExperiments(e);
    } catch (err) {
      setError("Failed to load experiments.");
    }
  }

  async function handleCreate(e) {
    e.preventDefault();
    setMessage(""); setError("");
    try {
      await experimentsApi.create({ title, slug, aim, objective, order_index: experiments.length + 1, is_published: true });
      setMessage("Experiment created.");
      setTitle(""); setSlug(""); setAim(""); setObjective("");
      loadExperiments();
    } catch (err) {
      setError(err.response?.data?.detail || "Creation failed");
    }
  }

  async function handleSetEvalSpec(e) {
    e.preventDefault();
    setMessage(""); setError("");
    if (!selectedExp) return;
    try {
      const parsedJson = JSON.parse(evalSpecJson);
      await experimentsApi.setEvalSpec(selectedExp.id, { expected_output: parsedJson, comparison_tolerance: 0.01 });
      setMessage(`Evaluation Spec updated for ${selectedExp.title}`);
    } catch (err) {
      setError(err instanceof SyntaxError ? "Invalid JSON" : err.response?.data?.detail || "Failed to update Eval Spec");
    }
  }

  return (
    <div className="admin-tab admin-grid">
      <div className="card">
        <h2 className="section-header">Create Experiment</h2>
        {message && <div className="alert alert--success mb-2">{message}</div>}
        {error && <div className="alert alert--error mb-2">{error}</div>}
        
        <form onSubmit={handleCreate} className="auth-form">
          <label className="form-label">
            Title
            <input className="form-input" value={title} onChange={e => setTitle(e.target.value)} required />
          </label>
          <label className="form-label">
            Slug
            <input className="form-input" value={slug} onChange={e => setSlug(e.target.value)} required pattern="^[a-z0-9-]+$" />
          </label>
          <label className="form-label">
            Aim
            <textarea className="form-textarea" value={aim} onChange={e => setAim(e.target.value)} required />
          </label>
          <label className="form-label">
            Objective
            <textarea className="form-textarea" value={objective} onChange={e => setObjective(e.target.value)} required />
          </label>
          <button className="btn btn--primary">Create Experiment</button>
        </form>
      </div>

      <div className="card">
        <h2 className="section-header">Manage Experiments</h2>
        <ul className="mb-2">
          {experiments.map(exp => (
            <li key={exp.id} className="mb-2" style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
              <div>
                <strong>{exp.title}</strong> <code>({exp.slug})</code>
              </div>
              <button 
                className="btn btn--ghost" 
                onClick={() => { setSelectedExp(exp); setEvalSpecJson('{\n  "accuracy": 0.85\n}'); }}
                style={{ padding: '4px 8px', fontSize: '0.8rem' }}
              >
                Configure
              </button>
            </li>
          ))}
          {experiments.length === 0 && <p className="admin-help">No experiments yet.</p>}
        </ul>

        {selectedExp && (
          <div style={{ marginTop: '2rem', borderTop: '1px solid var(--color-border)', paddingTop: '1rem' }}>
            <h3 className="section-header" style={{fontSize: '1rem'}}>Set Evaluation Spec: {selectedExp.title}</h3>
            <p className="admin-help">JSON representing the expected output dictionary to compare against client execution.</p>
            <form onSubmit={handleSetEvalSpec} className="auth-form">
              <textarea 
                className="form-textarea" 
                value={evalSpecJson} 
                onChange={e => setEvalSpecJson(e.target.value)} 
                rows={6}
                required 
                style={{ fontFamily: 'monospace' }}
              />
              <button className="btn btn--primary">Save Eval Spec</button>
            </form>
          </div>
        )}
      </div>
    </div>
  );
}
