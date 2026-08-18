document.addEventListener('DOMContentLoaded', () => {
  // Tab Switching
  const tabBtns = document.querySelectorAll('.tab-btn');
  const tabContents = document.querySelectorAll('.tab-content');

  tabBtns.forEach(btn => {
    btn.addEventListener('click', () => {
      tabBtns.forEach(b => b.classList.remove('active'));
      tabContents.forEach(c => c.classList.remove('active'));

      btn.classList.add('active');
      const target = btn.getAttribute('data-tab');
      document.getElementById(target).classList.add('active');
    });
  });

  // Mode toggle text update
  const modeToggle = document.getElementById('mode-toggle');
  const modeText = document.getElementById('mode-text');
  if (modeToggle && modeText) {
    modeToggle.addEventListener('change', () => {
      if (modeToggle.checked) {
        modeText.textContent = 'Concept (Draft)';
        modeText.style.color = '#f59e0b';
      } else {
        modeText.textContent = 'Definitief (Indienen)';
        modeText.style.color = '#10b981';
      }
    });
  }

  // Load Profile Defaults
  async function loadProfile() {
    try {
      const res = await fetch('/api/profile');
      if (res.ok) {
        const prof = await res.json();
        for (const [key, val] of Object.entries(prof)) {
          const input = document.getElementById(`prof-${key}`);
          if (input) {
            input.value = val;
          }
        }
      }
    } catch (e) {
      console.error('Failed to load profile:', e);
    }
  }

  loadProfile();

  // Profile Form Submit
  const profileForm = document.getElementById('profile-form');
  const profileResult = document.getElementById('profile-result');
  if (profileForm) {
    profileForm.addEventListener('submit', async (e) => {
      e.preventDefault();
      const formData = new FormData(profileForm);
      const data = {};
      formData.forEach((val, key) => { data[key] = val; });

      profileResult.classList.add('hidden');
      profileResult.className = 'result-box';
      profileResult.textContent = 'Profiel opslaan...';
      profileResult.classList.remove('hidden');

      try {
        const res = await fetch('/api/profile', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify(data)
        });
        const out = await res.json();
        if (out.status === 'success') {
          profileResult.textContent = 'Profielinstellingen succesvol bijgewerkt!';
        }
      } catch (err) {
        profileResult.classList.add('error');
        profileResult.textContent = 'Fout bij opslaan: ' + err.message;
      }
    });
  }

  // Single Form Submit
  const singleForm = document.getElementById('single-form');
  const singleResult = document.getElementById('single-result');
  const submitSingleBtn = document.getElementById('btn-submit-single');

  if (singleForm) {
    singleForm.addEventListener('submit', async (e) => {
      e.preventDefault();
      
      const isDraft = document.getElementById('mode-toggle').checked;
      const formData = new FormData(singleForm);
      const data = { isDraft: isDraft };
      
      formData.forEach((val, key) => { data[key] = val; });

      submitSingleBtn.disabled = true;
      submitSingleBtn.innerHTML = 'Bezig met versturen naar SPIN...';

      singleResult.classList.add('hidden');
      singleResult.className = 'result-box';
      singleResult.textContent = 'SPIN Robot is ingelogd en verwerkt de melding... (dit duurt ca. 15-20 seconden)';
      singleResult.classList.remove('hidden');

      try {
        const res = await fetch('/api/create-single', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify(data)
        });
        const out = await res.json();

        if (out.success) {
          singleResult.textContent = out.message || 'Melding succesvol verwerkt in SPIN!';
        } else {
          singleResult.classList.add('error');
          singleResult.textContent = 'Fout in SPIN: ' + (out.message || 'Verwerking mislukt.');
        }
      } catch (err) {
        singleResult.classList.add('error');
        singleResult.textContent = 'Fout bij verbinden met server: ' + err.message;
      } finally {
        submitSingleBtn.disabled = false;
        submitSingleBtn.innerHTML = `
          <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><line x1="22" y1="2" x2="11" y2="13"/><polygon points="22 2 15 22 11 13 2 9 22 2"/></svg>
          Maatregel Versturen naar SPIN
        `;
      }
    });
  }

  // Batch Excel File selection & Upload
  const fileInput = document.getElementById('excel-file');
  const fileNameDisplay = document.getElementById('selected-filename');
  const batchForm = document.getElementById('batch-form');
  const batchProgress = document.getElementById('batch-progress');
  const batchTableContainer = document.getElementById('batch-status-table-container');

  if (fileInput) {
    fileInput.addEventListener('change', () => {
      if (fileInput.files.length > 0) {
        fileNameDisplay.textContent = 'Geselecteerd: ' + fileInput.files[0].name;
      }
    });
  }

  if (batchForm) {
    batchForm.addEventListener('submit', async (e) => {
      e.preventDefault();
      if (!fileInput.files || fileInput.files.length === 0) {
        alert('Selecteer eerst een Excel bestand.');
        return;
      }

      const file = fileInput.files[0];
      const isDraft = document.getElementById('batch-draft-toggle').checked;

      const bodyData = new FormData();
      bodyData.append('file', file);
      bodyData.append('is_draft', isDraft);

      batchProgress.classList.remove('hidden');
      batchTableContainer.innerHTML = '<p style="color:#94a3b8">Excel bestand wordt geanalyseerd en verwerkt in SPIN... Even geduld.</p>';

      try {
        const res = await fetch('/api/import-excel', {
          method: 'POST',
          body: bodyData
        });
        const out = await res.json();

        let tableHtml = `
          <table style="width:100%; border-collapse:collapse; margin-top:12px; font-size:0.9rem;">
            <thead>
              <tr style="border-bottom:1px solid #475569; text-align:left; color:#38bdf8;">
                <th style="padding:8px;">Rij</th>
                <th style="padding:8px;">Weg</th>
                <th style="padding:8px;">Starttijd</th>
                <th style="padding:8px;">Eindtijd</th>
                <th style="padding:8px;">Status</th>
              </tr>
            </thead>
            <tbody>
        `;

        out.results.forEach(r => {
          const statusText = r.success ? '<span style="color:#10b981; font-weight:600;">✓ Verwerkt</span>' : '<span style="color:#ef4444; font-weight:600;">✗ Fout</span>';
          tableHtml += `
            <tr style="border-bottom:1px solid #334155;">
              <td style="padding:8px;">${r.row}</td>
              <td style="padding:8px;">${r.road || '-'}</td>
              <td style="padding:8px;">${r.start || '-'}</td>
              <td style="padding:8px;">${r.end || '-'}</td>
              <td style="padding:8px;">${statusText}</td>
            </tr>
          `;
        });

        tableHtml += '</tbody></table>';
        batchTableContainer.innerHTML = tableHtml;

      } catch (err) {
        batchTableContainer.innerHTML = `<p style="color:#ef4444">Fout bij batch verwerking: ${err.message}</p>`;
      }
    });
  }
});
