/**
 * @file Esup-Pod speaker management script.
 */
document.addEventListener('DOMContentLoaded', function() {
  /**
   * Adds a job field to the job fields container.
   * @param {string} jobId - The ID of the job (default is an empty string).
   * @param {string} jobTitle - The title of the job (default is an empty string).
   */
  function addJobField(jobId = '', jobTitle = '') {
    var jobFieldHtml = `
       <div class="d-flex align-items-center job-content">
        <input type="text" class="form-control jobTitle" name="jobs[]" value="${jobTitle}" placeholder="${gettext("Job title")}">
        <input type="hidden" class="jobId" name="jobIds[]" value="${jobId}">
        <a title="${gettext("Remove job")}" role="button" class="btn btn-link pod-btn-social remove-job-field"><i class="bi bi-trash"></i></a>
      </div>
    `;
    document.getElementById('jobFieldsContainer').insertAdjacentHTML('beforeend', jobFieldHtml);
  }

  /**
   * Shows the add/edit speaker modal with the provided speaker data.
   * @param {Object|null} speaker - The speaker data (default is null for adding a new speaker).
   */
  function showSpeakerModal(speaker = null) {
    // Clear existing job fields
    document.getElementById('jobFieldsContainer').textContent = '';

    if (speaker) {
      // Editing speaker
      document.getElementById('speakerModalLabel').textContent = gettext("Edit this speaker");
      document.getElementById('actionField').value = 'edit';
      document.getElementById('speakerId').value = speaker.id;
      document.getElementById('id_firstname').value = speaker.firstname;
      document.getElementById('id_lastname').value = speaker.lastname;

      // Fetch and populate jobs
      fetch(`/speaker/get-jobs/${speaker.id}/`)
        .then(response => response.json())
        .then(data => {
          data.jobs.forEach(job => {
            addJobField(job.id, job.title);
          });
        })
        .catch(error => {
          console.error('Error fetching jobs:', error);
        });
    } else {
      // Adding new speaker
      document.getElementById('speakerModalLabel').textContent = gettext("Add a speaker");
      document.getElementById('actionField').value = 'add';
      document.getElementById('speakerId').value = '';
      document.getElementById('id_firstname').value = '';
      document.getElementById('id_lastname').value = '';
      addJobField(); // Add one empty job field by default
    }

    // Show modal
    var speakerModal = new bootstrap.Modal(document.getElementById('speakerModal'));
    speakerModal.show();
  }

  // Add job field on button click
  document.getElementById('add-job-field').addEventListener('click', function() {
    addJobField();
  });

  // Remove job field on button click
  document.addEventListener('click', function(event) {
    if (event.target && event.target.closest('.remove-job-field')) {
      event.target.closest('.job-content').remove();
    }
  });

  // Set up event listeners for add/edit buttons
  document.querySelectorAll('.add-speaker-btn').forEach(button => {
    button.addEventListener('click', function() {
      showSpeakerModal();
    });
  });

  document.querySelectorAll('.edit-speaker-field').forEach(button => {
    button.addEventListener('click', function() {
      var speakerId = this.getAttribute('data-speaker-id');

      // Fetch speaker data (you may need to implement this endpoint)
      fetch(`/speaker/get-speaker/${speakerId}/`)
        .then(response => response.json())
        .then(data => {
          showSpeakerModal(data.speaker);
        })
        .catch(error => {
          console.error('Error fetching speaker:', error);
        });
    });
  });
});
