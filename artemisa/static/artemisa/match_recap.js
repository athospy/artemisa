function getCsrfToken() {
    const name = 'csrftoken=';
    const decodedCookie = decodeURIComponent(document.cookie);
    const parts = decodedCookie.split(';');
    for (let i = 0; i < parts.length; i++) {
        let c = parts[i];
        while (c.charAt(0) === ' ') {
            c = c.substring(1);
        }
        if (c.indexOf(name) === 0) {
            return c.substring(name.length, c.length);
        }
    }
    return '';
}

const csrfToken = getCsrfToken();

document.addEventListener('DOMContentLoaded', function() {
    const button = document.querySelector('#generate_recap_btn');
    const statusEl = document.querySelector('#recap_status');
    const textEl = document.querySelector('#recap_text');

    button.addEventListener('click', function() {
        const competitionId = button.dataset.competition_id;
        button.disabled = true;
        statusEl.textContent = 'Generating recap...';
        textEl.textContent = '';

        fetch(`/generate_match_recap/${competitionId}`, {
            method: 'POST',
            headers: {
                'X-CSRFToken': csrfToken,
            },
        })
        .then(response => response.json().then(data => ({ ok: response.ok, data })))
        .then(({ ok, data }) => {
            if (ok) {
                statusEl.textContent = '';
                textEl.textContent = data.recap;
            } else {
                statusEl.textContent = data.error || 'Something went wrong.';
            }
        })
        .catch(() => {
            statusEl.textContent = 'Something went wrong.';
        })
        .finally(() => {
            button.disabled = false;
        });
    });
});
