import React, { useState, useEffect } from 'react';
import { Plus, Edit2, Trash2, X, Eye, EyeOff, Archive, CheckCircle } from 'lucide-react';
import './DraftManagement.css';
import axios from 'axios';

const DraftManagement = () => {
  const [drafts, setDrafts] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    fetchDrafts();
  }, []);

  const fetchDrafts = async () => {
    try {
      setLoading(true);
      const res = await axios.get('http://localhost:5000/api/drafts');
      setDrafts(res.data);
      setLoading(false);
    } catch (err) {
      console.error('Error fetching drafts:', err);
      setError('Failed to fetch drafts Workspace Error. The server may be unreachable.');
      setDrafts([]);
      setLoading(false);
    }
  };

  const [isModalOpen, setIsModalOpen] = useState(false);
  const [isEditing, setIsEditing] = useState(false);
  const [currentDraft, setCurrentDraft] = useState(null);

  const [formData, setFormData] = useState({
    title: '',
    startDate: '',
    endDate: '',
    file: null,
  });

  const [formError, setFormError] = useState('');

  // Helpers
  const getStatus = (draft) => {
    // Hard overrides: if the Admin manually closed/archived via the toggle button
    if (draft.status === 'closed')   return { label: 'Closed',   class: 'status-closed' };
    if (draft.status === 'archived') return { label: 'Archived', class: 'status-archived' };

    const now = new Date();

    // Use closed_at (explicit closing date) if present, otherwise fall back to endDate
    const closingBoundary = draft.closed_at
      ? new Date(draft.closed_at)
      : new Date(draft.endDate);
    closingBoundary.setHours(23, 59, 59, 999);

    const openBoundary = new Date(draft.startDate);

    if (now < openBoundary) {
      return { label: 'Upcoming', class: 'status-upcoming' };
    }

    // Active: status is 'open' in DB AND current date is still within the window
    if (draft.status === 'open' && now <= closingBoundary) {
      return { label: 'Active', class: 'status-active' };
    }

    // Past the closing date regardless of DB status
    return { label: 'Expired', class: 'status-closed' };
  };

  const handleOpenModal = (draft = null) => {
    if (draft) {
      setIsEditing(true);
      setCurrentDraft(draft);
      setFormData({
        title: draft.title,
        startDate: draft.startDate,
        endDate: draft.endDate,
        file: draft.file,
      });
    } else {
      setIsEditing(false);
      setCurrentDraft(null);
      setFormData({
        title: '',
        startDate: '',
        endDate: '',
        file: null,
      });
    }
    setFormError('');
    setIsModalOpen(true);
  };

  const handleCloseModal = () => {
    setIsModalOpen(false);
    setFormError('');
  };

  const handleFileChange = (e) => {
    const file = e.target.files[0];
    if (file) {
      if (file.type !== 'application/pdf') {
        setFormError('Only PDF files are allowed.');
        return;
      }
      setFormData({ ...formData, file });
      setFormError('');
    }
  };

  const handleSave = () => {
    if (!formData.title || !formData.startDate || !formData.endDate) {
      setFormError('Please fill in all required fields.');
      return;
    }

    if (new Date(formData.endDate) < new Date(formData.startDate)) {
      setFormError('End date cannot be before start date.');
      return;
    }

    if (!isEditing && !formData.file) {
      setFormError('Please upload a PDF file.');
      return;
    }

    if (isEditing) {
      axios.put(`http://localhost:5000/api/admin/update-draft/${currentDraft.id}`, {
        startDate: formData.startDate,
        endDate: formData.endDate
      }).then((res) => {
        if (res.status === 200) {
          setDrafts(drafts.map(d => 
            d.id === currentDraft.id 
              ? { ...d, title: formData.title, startDate: formData.startDate, endDate: formData.endDate, file: formData.file || d.file } 
              : d
          ));
        }
      }).catch(err => setFormError("Failed to save dates in database."));
    } else {
      const newDraft = {
        id: `D-${new Date().getFullYear()}-00${drafts.length + 10}`,
        title: formData.title,
        uploadDate: new Date().toISOString().split('T')[0],
        startDate: formData.startDate,
        endDate: formData.endDate,
        file: formData.file,
        isManuallyClosed: false,
      };
      setDrafts([newDraft, ...drafts]);
    }
    handleCloseModal();
  };

  const handleCsvUpload = (e, draftId) => {
    const file = e.target.files[0];
    if (file && file.type === "text/csv") {
      const reader = new FileReader();
      reader.onload = async (event) => {
        const text = event.target.result;
        // Basic CSV parsing
        const lines = text.split('\n').filter(line => line.trim() !== '');
        if (lines.length < 2) {
          alert("CSV is empty or missing data rows.");
          return;
        }
        
        // Assume simple CSV or just treating every non-header line as a comment
        const comments = lines.slice(1).map(line => ({
          draft_id: draftId,
          text: line.replace(/^"|"$/g, '')
        }));
        
        try {
          alert(`Uploading ${comments.length} comments for bulk analysis... This might take a moment.`);
          const res = await fetch('http://localhost:5000/api/analyze/bulk', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ comments })
          });
          const data = await res.json();
          alert(`Success! Analyzed and inserted ${data.inserted_count} comments.`);
        } catch (err) {
          console.error(err);
          alert('Error uploading comments for bulk analysis.');
        }
      };
      reader.readAsText(file);
    } else {
      alert("Please upload a valid CSV file.");
    }
    // reset input
    e.target.value = null;
  };

  const toggleCloseConsultation = async (id, currentlyClosed) => {
    const newStatus = currentlyClosed ? 'open' : 'closed';
    try {
      await axios.put(`http://localhost:5000/api/admin/update-draft/${id}`, {
        status: newStatus
      });
      // Re-fetch to reflect the persisted change
      await fetchDrafts();
    } catch (err) {
      console.error('Failed to toggle draft status:', err);
      alert('Could not update draft status. Please try again.');
    }
  };

  const handleViewPdf = (file) => {
    if (file && file instanceof Blob) {
      const fileURL = URL.createObjectURL(file);
      window.open(fileURL, "_blank");
    } else {
      alert("No local file uploaded. In a real app, this would fetch from backend.");
    }
  };

  return (
    <div className="draft-management">
      <div className="page-header">
        <div className="header-text">
          <h2>Draft Management (Admin)</h2>
          <p>Create, update, and manage public consultation drafts securely.</p>
        </div>
        <div className="header-actions">
          <button className="btn-primary" onClick={() => handleOpenModal()}>
            <Plus size={18} /> Add New Draft
          </button>
        </div>
      </div>

      {error && <div className="error-banner" style={{marginBottom: '1rem'}}>{error}</div>}

      <div className="panel-white">
        <div className="table-responsive">
          <table className="draft-table">
            <thead>
              <tr>
                <th>Draft Title</th>
                <th>Upload Date</th>
                <th>Consultation Period</th>
                <th>Status</th>
                <th>Actions</th>
              </tr>
            </thead>
            <tbody>
              {drafts.map(draft => {
                const status = getStatus(draft);
                return (
                  <tr key={draft.id}>
                    <td>
                      <div className="draft-title">{draft.title}</div>
                      <div className="draft-id">{draft.id}</div>
                    </td>
                    <td>{draft.uploadDate}</td>
                    <td>
                      {draft.startDate} <br /> 
                      <small className="text-secondary">to</small> {draft.endDate}
                    </td>
                    <td>
                      <span className={`status-badge ${status.class}`}>{status.label}</span>
                    </td>
                    <td>
                      <div className="action-buttons">
                        <label className="btn-icon csv-upload-btn" title="Upload Comments CSV">
                          <input type="file" accept=".csv" style={{display: 'none'}} onChange={(e) => handleCsvUpload(e, draft.id)} />
                          <Plus size={18} />
                        </label>
                        <button 
                          className="btn-icon" 
                          onClick={() => handleViewPdf(draft.file)}
                          title="View PDF"
                        >
                          <Eye size={18} />
                        </button>
                        <button 
                          className="btn-icon" 
                          onClick={() => handleOpenModal(draft)}
                          title="Edit Dates & Title"
                        >
                          <Edit2 size={18} />
                        </button>
                        <button 
                          className={`btn-icon ${draft.status === 'closed' ? 'text-success' : 'text-danger'}`} 
                          onClick={() => toggleCloseConsultation(draft.id, draft.status === 'closed')}
                          title={draft.status === 'closed' ? "Reopen Consultation" : "Close Consultation"}
                        >
                          {draft.status === 'closed' ? <CheckCircle size={18} /> : <Archive size={18} />}
                        </button>
                      </div>
                    </td>
                  </tr>
                );
              })}
              {drafts.length === 0 && (
                <tr>
                  <td colSpan="5" className="empty-state">No drafts available. Click "Add New Draft" to create one.</td>
                </tr>
              )}
            </tbody>
          </table>
        </div>
      </div>

      {isModalOpen && (
        <div className="modal-overlay">
          <div className="modal-content">
            <div className="modal-header">
              <h3>{isEditing ? 'Edit Draft Details' : 'Upload New Draft'}</h3>
              <button className="btn-close" onClick={handleCloseModal}><X size={20} /></button>
            </div>
            <div className="modal-body">
              {formError && <div className="error-banner">{formError}</div>}
              
              <div className="form-group">
                <label>Document Title <span className="required">*</span></label>
                <input 
                  type="text" 
                  className="form-control"
                  value={formData.title} 
                  onChange={(e) => setFormData({...formData, title: e.target.value})}
                  placeholder="e.g. Health Protection Act"
                />
              </div>

              <div className="form-group document-upload">
                <label>PDF File <span className="required">{!isEditing && '*'}</span></label>
                <input 
                  type="file" 
                  accept="application/pdf"
                  className="form-control-file"
                  onChange={handleFileChange}
                />
                {isEditing && !formData.file && currentDraft?.file === null && (
                  <small className="file-notice">No file currently uploaded. You can attach one.</small>
                )}
                {formData.file && (
                  <small className="file-selected">Selected: {formData.file.name}</small>
                )}
              </div>

              <div className="form-row">
                <div className="form-group half-width">
                  <label>Consultation Start Date <span className="required">*</span></label>
                  <input 
                    type="date" 
                    className="form-control"
                    value={formData.startDate} 
                    onChange={(e) => setFormData({...formData, startDate: e.target.value})}
                  />
                </div>
                <div className="form-group half-width">
                  <label>Consultation End Date <span className="required">*</span></label>
                  <input 
                    type="date" 
                    className="form-control"
                    value={formData.endDate} 
                    onChange={(e) => setFormData({...formData, endDate: e.target.value})}
                  />
                </div>
              </div>

            </div>
            <div className="modal-footer">
              <button className="btn-secondary" onClick={handleCloseModal}>Cancel</button>
              <button className="btn-primary" onClick={handleSave}>
                {isEditing ? 'Save Changes' : 'Upload Draft'}
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default DraftManagement;
