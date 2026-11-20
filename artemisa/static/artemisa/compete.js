document.addEventListener('DOMContentLoaded', function() {
    document.querySelector('#select_category').addEventListener('change', select_category);
    // Event delegation for button labels (Bootstrap handles the checkbox internally)
    document.addEventListener('click', function(e) {
        // Check if clicked element is the label or inside the button group
        const label = e.target.closest('.btn-group-toggle label');
        if (label) {
            const checkbox = label.querySelector('.archer-checkbox');
            if (checkbox) {
                // Small delay to let Bootstrap update the checkbox state
                setTimeout(update_selected_archers, 50);
            }
        }
    });

    // Auto-select first category and check all archers to restore scores
    const selectEl = document.querySelector('#select_category');
    if (selectEl && selectEl.options.length > 1) {
        selectEl.selectedIndex = 1;
        select_category();
        const firstCategoryId = selectEl.value;
        const dropdown = document.querySelector(`#category_${firstCategoryId}`);
        if (dropdown) {
            const labels = dropdown.querySelectorAll('label.btn');
            labels.forEach(label => {
                const cb = label.querySelector('.archer-checkbox');
                if (cb) {
                    cb.checked = true;
                    label.classList.add('active');
                }
            });
            update_selected_archers();
        }
    }
});

function getCsrfToken() {
    const name = 'csrftoken=';
    const decodedCookie = decodeURIComponent(document.cookie);
    const ca = decodedCookie.split(';');
    for (let i = 0; i < ca.length; i++) {
        let c = ca[i];
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

// hide all the archers and only show the selected one and put the 'active'in the button for highlight
function change_archer(event) {
    const archer_id = event.target.dataset.archer_id;
    const shoots_scores = document.querySelectorAll(`.archer_container_div`);
    shoots_scores.forEach(el => {
        el.style.display = 'none';
    });

    const archer_div = document.querySelector(`#archer_${archer_id}`);
    archer_div.style.display = 'block';

    const archer_buttons = document.querySelectorAll(`.archer_picker`);
    archer_buttons.forEach(el => {
        el.classList.remove("active");
    });
    event.target.classList.add("active");

}

// only show the archer of the category selected
function select_category() {
    const category_id = document.querySelector('#select_category').value;
    // hide all dropdowns
    const dropdowns = document.querySelectorAll('.categories_dropdown');
    dropdowns.forEach(el => el.style.display = 'none');
    // only show the selected one
    const dropdown_selected = document.querySelector(`#category_${category_id}`);
    if (dropdown_selected) {
        dropdown_selected.style.display = 'block';
    }
    // Clear any previously selected archers
    document.querySelector('#archer_button_picker').innerHTML = '';
    document.querySelector('#archers_container').innerHTML = '';
}

// Update archers based on checkbox selection
function update_selected_archers() {
    const checked_checkboxes = document.querySelectorAll('.archer-checkbox:checked');
    const archers_ids = Array.from(checked_checkboxes).map(cb => cb.dataset.archerId);
    set_score_forms(archers_ids);
}

// fist empty the buttons and archer container then add for preventing repetition
function set_score_forms(archers_ids) {
    console.log(`archers_ids: ${archers_ids}`)
    document.querySelector('#archer_button_picker').innerHTML = '';
    document.querySelector('#archers_container').innerHTML = '';
    // dont add the same archer
    archers_ids.forEach((archer_id) => {
        add_archer(archer_id);
    });
}

// add the archer button and request the archer_div for adding a scoring system for every archer
function add_archer(archer_id) {
    const archer_button_picker = document.querySelector('#archer_button_picker');
    const archers = document.querySelector('#archers_map').dataset.archers;
    const archer_map = JSON.parse(archers);
    archer_button_picker.insertAdjacentHTML(
        'beforeend',
        `<button type="button" class="btn btn-outline-primary btn-lg mx-2 archer_picker" data-archer_id="${archer_id}">${archer_map[archer_id]}</button>`
    );
    fetch(`/add_archer_div`, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'X-CSRFToken': csrfToken,
        },
        body: JSON.stringify({
            archer_id: archer_id,
        })
    })
    .then(response => response.text())
    .then(result => {
        // the result is html, so just put it in the div
        document.querySelector('#archers_container').insertAdjacentHTML(
            'beforeend',
            result
        );
        // add the listener for the recent html added
        const divs = document.querySelectorAll(`.archer_picker`);
        divs.forEach(el => el.addEventListener('click', change_archer));
        // add the first end for the added archer
        add_score_div(archer_id, 1);
        // Load any previously saved scores for this archer/category
        load_saved_scores(archer_id);
    })
    .catch(error => {
        console.log(error)
    });


}
// and the 'end' scorring row for the archer requesting for the score_div html
function add_score_div(archer_id, end_number) {
    const container_div = document.querySelector(`#archer_${archer_id}_scores_div`);
    fetch(`/add_score_div`, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'X-CSRFToken': csrfToken,
        },
        body: JSON.stringify({
            end_number: end_number,
            archer_id: archer_id,
        })
    })
    .then(response => response.text())
    .then(result => {
        // the result is html, so just put it in the div
        document.querySelector(`#archer_${archer_id}_scores_div`).insertAdjacentHTML(
            'beforeend',
            result
        );
        // add the listener for the recent html added
        const divs = document.querySelectorAll(`#archer_${archer_id} .shoot_input`);
        divs.forEach(el => el.addEventListener('change', add_score));
        const end_button = document.querySelector(`#archer_${archer_id}_end_${end_number}_button`);
        end_button.addEventListener('click', add_shoot_end);
        init_virtual_keyboard();
        highlight_inputs_focus();
    })
    .catch(error => {
        console.log(error)
    });
}

// Fetch saved scores and populate UI
function load_saved_scores(archer_id) {
    const category_id = document.querySelector('#select_category').value;
    fetch(`/get_archer_scores`, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'X-CSRFToken': csrfToken,
        },
        body: JSON.stringify({ archer_id, category_id })
    })
    .then(r => r.json())
    .then(({scores}) => {
        if (!scores || scores.length === 0) {
            return; // nothing to restore
        }
        const grouped = {};
        let maxEnd = 0;
        scores.forEach(s => {
            const e = s.end_number;
            if (!grouped[e]) grouped[e] = [];
            grouped[e][s.shoot_number - 1] = s.score; // index 0..5
            if (e > maxEnd) maxEnd = e;
        });

        // Fill end 1 if already present
        if (grouped[1]) {
            fill_saved_end(archer_id, 1, grouped[1]);
        }
        // Add and fill the other ends one after another, in end order. Requesting them
        // all at once inserted each end when its response arrived, so ends (and their
        // running totals) could appear out of order after a reload.
        const ends = Object.keys(grouped).map(Number).filter(e => e !== 1).sort((a, b) => a - b);
        let chain = Promise.resolve();
        ends.forEach(endNum => {
            chain = chain.then(() => add_score_div_then_fill(archer_id, endNum, grouped[endNum]));
        });

        // Then add the next empty end to continue scoring
        chain.then(() => {
            if (maxEnd < 12) {
                add_score_div(archer_id, maxEnd + 1);
            }
        });
    })
    .catch(err => console.log(err));
}

function add_score_div_then_fill(archer_id, end_number, scoresArray) {
    return fetch(`/add_score_div`, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'X-CSRFToken': csrfToken,
        },
        body: JSON.stringify({ end_number, archer_id })
    })
    .then(response => response.text())
    .then(result => {
        document.querySelector(`#archer_${archer_id}_scores_div`).insertAdjacentHTML('beforeend', result);
        const divs = document.querySelectorAll(`#archer_${archer_id} .shoot_input`);
        divs.forEach(el => el.addEventListener('change', add_score));
        const end_button = document.querySelector(`#archer_${archer_id}_end_${end_number}_button`);
        end_button.addEventListener('click', add_shoot_end);
        init_virtual_keyboard();
        highlight_inputs_focus();
        fill_saved_end(archer_id, end_number, scoresArray);
    })
    .catch(error => console.log(error));
}

function fill_saved_end(archer_id, end_number, scoresArray) {
    // Reset end totals based on current final total
    init_zero_end(end_number, archer_id);
    for (let i = 0; i < 6; i++) {
        const score = (scoresArray[i] || '').toString().toUpperCase();
        const input = document.querySelector(`#archer_${archer_id}_end_${end_number}_shoot_${i+1}`);
        if (!input) continue;
        input.value = score;
        const numeric = check_score_transform(score, end_number, archer_id);
        sum_score(numeric, end_number, archer_id);
    }
    // Disable inputs and hide Next button for restored ends
    const inputs = document.querySelectorAll(`#archer_${archer_id}_end_${end_number} .shoot_input`);
    inputs.forEach(el => {
        el.disabled = "disabled";
        el.classList.remove("shoot_input");
        el.classList.remove('highlighted');
    });
    const end_button = document.querySelector(`#archer_${archer_id}_end_${end_number}_button`);
    if (end_button) end_button.style.display = 'none';
    sum_end_totals(end_number, archer_id);
    if (parseInt(end_number) === 6) {
        document.querySelector(`#archer_${archer_id}_scores_div`).insertAdjacentHTML('beforeend','<hr><hr><div>End of round 1</div><hr><hr>');
    }
    if (parseInt(end_number) === 12) {
        document.querySelector(`#archer_${archer_id}_scores_div`).insertAdjacentHTML('beforeend','<hr><hr><div>End of round 2</div><hr><hr>');
    }
}

// check valid and loop for every 6 inputs for adding the score and check if is and 'x' or a '10' for adding in each score respectively
// loop through each input every time for preventing error when editing scores
// transforming de 'X' to 10 and the 'M' to 0 for the scoring
function add_score(event) {
    let scoreValue = (event.target.value || '').toUpperCase();
    if (!is_score_valid(scoreValue)) {
        alert(`Invalid score ${scoreValue}. Use 0-10, X or M.`);
        event.target.value = '';
        return;
    }
    event.target.value = scoreValue;
    const end_number = event.target.dataset.end;
    const archer_id = event.target.dataset.archer_id;
    const shoot_number = event.target.dataset.shoot;
    init_zero_end(end_number, archer_id);
    const shoots_scores = document.querySelectorAll(`#archer_${archer_id} .shoot_input`);
    let all_scores_input_filled = true;
    let shoot_array = [];
    shoots_scores.forEach((el, index) => {
        if (is_empty(el.value)) {
            all_scores_input_filled = false;
        }
        let score = el.value.toUpperCase() || 0;
        shoot_array.push(score);
        score = check_score_transform(score, end_number, archer_id);
        sum_score(score, end_number, archer_id);
    });
    // if all the inpunt has value proceed to the next end if there is one
    // after 6 ends the first roung is over and after 12 ends the tournament is over
    if (all_scores_input_filled) {
        // show next end button
        const end_button = document.querySelector(`#archer_${archer_id}_end_${end_number}_button`);
        end_button.style.display = 'block';
    }
    else {
        event.target.classList.remove('highlighted');
        // focus on the next input
        document.querySelector(`#archer_${archer_id}_end_${end_number}_shoot_${parseInt(shoot_number)+1}`).click();
    }

}

function add_shoot_end(event) {
    const end_number = event.target.dataset.end;
    const archer_id = event.target.dataset.archer_id;
    const shoots_scores = document.querySelectorAll(`#archer_${archer_id} .shoot_input`);
    let shoot_array = [];
    shoots_scores.forEach(el => {
        let score = el.value.toUpperCase() || 0;
        shoot_array.push(score);
    });
    save_score_db(shoot_array, archer_id, end_number);
    shoots_scores.forEach(el => {
        el.disabled = "disabled";
        el.classList.remove("shoot_input");
        el.classList.remove('highlighted');
    });
    sum_end_totals(end_number, archer_id);
    if (parseInt(end_number) == 6) {
        document.querySelector(`#archer_${archer_id}_scores_div`).insertAdjacentHTML(
            'beforeend',
            '<hr><hr><div>End of round 1</div><hr><hr>'
        );
    }
    if (parseInt(end_number) == 12) {
        document.querySelector(`#archer_${archer_id}_scores_div`).insertAdjacentHTML(
            'beforeend',
            '<hr><hr><div>End of round 2</div><hr><hr>'
        );
    }
    else {
        add_score_div(archer_id, parseInt(end_number)+1);
    }
    event.target.style.display = 'none';
}

// after the 'end' if complete save the score in the database
function save_score_db(shoot_array, archer_id, end_number) {
    const category_id = document.querySelector('#select_category').value;
    fetch(`/save_score_db`, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'X-CSRFToken': csrfToken,
        },
        body: JSON.stringify({
            shoot_array: shoot_array,
            archer_id: archer_id,
            end_number: end_number,
            category_id: category_id,
        })
    })
    .then(response => response.json())
    .then(result => {
        console.log(result);
    })
    .catch(error => {
        console.log(error)
    });
}

function is_empty(str) {
 return !str.trim().length;
}

function is_score_valid(score) {
    if (score === 'M' || score === 'X') {
        return true;
    }
    const numeric = parseInt(score, 10);
    if (Number.isNaN(numeric)) {
        return false;
    }
    return numeric >= 0 && numeric <= 10;
}

// before adding put everything to zero or adding the last final score from partials
function init_zero_end(end_number, archer_id) {
    const partial_div = document.querySelector(`#archer_${archer_id}_end_${end_number}_partial`);
    partial_div.value = 0;
    const total_div = document.querySelector(`#archer_${archer_id}_end_${end_number}_total`);
    const final_total_div = document.querySelector(`#archer_${archer_id}_final_total`);
    total_div.value = parseInt(final_total_div.value);
    // console.log(`total: ${parseInt(final_total_div.value)}`);
    const tens_div = document.querySelector(`#archer_${archer_id}_end_${end_number}_10s`);
    tens_div.value = 0;
    const xs_div = document.querySelector(`#archer_${archer_id}_end_${end_number}_xs`);
    xs_div.value = 0;
}

// input validation and letter to score number conversion
function check_score_transform(score, end_number, archer_id) {
    if (score == 10) {
        add_10s(end_number, archer_id);
    }
    if (score == "M") {
        score = 0;
    }
    if (score == 'X') {
        add_xs(end_number, archer_id);
        add_10s(end_number, archer_id);
        score = 10;
    }
    return parseInt(score);
}

function add_10s(end_number, archer_id) {
    const tens_div = document.querySelector(`#archer_${archer_id}_end_${end_number}_10s`);
    const tens_value = parseInt(tens_div.value) || 0;
    tens_div.value = tens_value + 1;
}

function add_xs(end_number, archer_id) {
    const xs_div = document.querySelector(`#archer_${archer_id}_end_${end_number}_xs`);
    const xs_value = parseInt(xs_div.value) || 0;
    xs_div.value = xs_value + 1;
}

function sum_score(score, end_number, archer_id) {
    sum_partial(score, end_number, archer_id);
    sum_total(score, end_number, archer_id);
}


function sum_partial(score, end_number, archer_id) {
    const partial_div = document.querySelector(`#archer_${archer_id}_end_${end_number}_partial`);
    const partial_value = parseInt(partial_div.value) || 0;
    partial_div.value = partial_value + score;
}


function sum_total(score, end_number, archer_id) {
    const total_div = document.querySelector(`#archer_${archer_id}_end_${end_number}_total`);
    const total_value = parseInt(total_div.value) || 0;
    total_div.value = total_value + score;
}

function sum_end_totals(end_number, archer_id) {
    const total_div = document.querySelector(`#archer_${archer_id}_end_${end_number}_partial`);
    sum_final_total(parseInt(total_div.value), archer_id);
    const tens_div = document.querySelector(`#archer_${archer_id}_end_${end_number}_10s`);
    sum_final_10s(parseInt(tens_div.value), archer_id);
    const xs_div = document.querySelector(`#archer_${archer_id}_end_${end_number}_xs`);
    sum_final_xs(parseInt(xs_div.value), archer_id);
}

function sum_final_total(score, archer_id) {
    const total_div = document.querySelector(`#archer_${archer_id}_final_total`);
    const total_value = parseInt(total_div.value) || 0;
    total_div.value = total_value + score;
}

function sum_final_10s(score, archer_id) {
    const final_tens_div = document.querySelector(`#archer_${archer_id}_final_10s`);
    const final_tens_value = parseInt(final_tens_div.value) || 0;
    final_tens_div.value = final_tens_value + score;
}

function sum_final_xs(score, archer_id) {
    const final_x_div = document.querySelector(`#archer_${archer_id}_final_xs`);
    const final_xs_value = parseInt(final_x_div.value) || 0;
    final_x_div.value = final_xs_value + score;
}

function init_virtual_keyboard() {

    KioskBoard.init({
        /*!
         * Required
         * An Array of Objects has to be defined for the custom keys.
         * Hint: Each object creates a row element (HTML) on the keyboard.
         * e.g. [{"key":"value"}, {"key":"value"}] => [{"0":"A","1":"B","2":"C"}, {"0":"D","1":"E","2":"F"}]
         */
        keysArrayOfObjects: [{"6": "6", "7": "7", "8": "8", "9": "9", "10": "10", "X": "X"}, {"M": "M", "1": "1", "2": "2", "3": "3", "4": "4", "5": "5"}],
    
        /*!
         * Required only if "keysArrayOfObjects" is "null".
         * The path of the "kioskboard-keys-${language}.json" file must be set to the "keysJsonUrl" option. (XMLHttpRequest to get the keys from JSON file.)
         * e.g. '/Content/Plugins/KioskBoard/dist/kioskboard-keys-english.json'
         */
        keysJsonUrl: null,
    
        /* 
         * Optional: (Special Characters)
         * An Array of Strings can be set to override the built-in special characters.
         * e.g. ["#", "€", "%", "+", "-", "*"]
         */
        keysSpecialCharsArrayOfStrings: null,
    
        /* 
         * Optional: (Numpad Keys)
         * An Array of Numbers can be set to override the built-in numpad keys. (From 0 to 9, in any order.)
         * e.g. [1, 2, 3, 4, 5, 6, 10, 9, 9, 0]
         */
        keysNumpadArrayOfNumbers: null,
    
        // Optional: (Other Options)
        // Language Code (ISO 639-1) for custom keys (for language support) => e.g. "de" || "en" || "fr" || "hu" || "tr" etc...
        language: 'en',
    
        // The theme of keyboard => "light" || "dark" || "flat" || "material" || "oldschool"
        theme: 'light',
    
        // Scrolls the document to the top or bottom(by the placement option) of the input/textarea element. Prevented when "false"
        autoScroll: true,
    
        // Uppercase or lowercase to start. Uppercased when "true"
        capsLockActive: true,
    
        // Allow or prevent real/physical keyboard usage. Prevented when "false"
        // In addition, the "allowMobileKeyboard" option must be "true" as well, if the real/physical keyboard has wanted to be used.
        allowRealKeyboard: false,
    
        // Allow or prevent mobile keyboard usage. Prevented when "false"
        allowMobileKeyboard: false,
    
        // CSS animations for opening or closing the keyboard
        cssAnimations: true,
    
        // CSS animations duration as millisecond
        cssAnimationsDuration: 90,
    
        // CSS animations style for opening or closing the keyboard => "slide" || "fade"
        cssAnimationsStyle: 'fade',
    
        // Enable or Disable Spacebar functionality on the keyboard. The Spacebar will be passive when "false"
        keysAllowSpacebar: false,
    
        // Text of the Space key (Spacebar). Without text => " "
        keysSpacebarText: 'Space',
    
        // Font family of the keys
        keysFontFamily: 'sans-serif',
    
        // Font size of the keys
        keysFontSize: '25px',
    
        // Font weight of the keys
        keysFontWeight: 'normal',
    
        // Size of the icon keys
        keysIconSize: '25px',
    
        // Text of the Enter key (Enter/Return). Without text => " "
        keysEnterText: 'Enter',
    
        // The callback function of the Enter key. This function will be called when the enter key has been clicked.
        keysEnterCallback: undefined,
    
        // The Enter key can close and remove the keyboard. Prevented when "false"
        keysEnterCanClose: false,
    });
    

    KioskBoard.run('.js-kioskboard-input', { 

    });
}

function highlight_inputs_focus() {
    const inputs = document.querySelectorAll('.js-kioskboard-input');

    inputs.forEach(input => {
        input.addEventListener('focus', function() {
            input.classList.add('highlighted');
        });

        input.addEventListener('blur', function() {
            input.classList.remove('highlighted');
        });

    });
}