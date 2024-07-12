document.addEventListener('DOMContentLoaded', function() {
    document.querySelector('#select_category').addEventListener('change', select_category);
    const divs = document.querySelectorAll(`.categories_dropdown`);
    divs.forEach(el => el.addEventListener('change', select_archers));
});

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
    document.querySelector('.categories_dropdown').style.display = 'none';
    // only show the selected one
    const dropdown_selected = document.querySelector(`#category_${category_id}`);
    if (dropdown_selected) {
        dropdown_selected.style.display = 'block';
    }
}

// add the archer buttons and form for every archer
function select_archers(event) {
    const selected = event.target.selectedOptions;
    var archers_ids = Array.from(selected).map(({ value }) => value);
    set_score_forms(archers_ids)
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

// check valid and loop for every 6 inputs for adding the score and check if is and 'x' or a '10' for adding in each score respectively
// loop through each input every time for preventing error when editing scores
// transforming de 'X' to 10 and the 'M' to 0 for the scoring
function add_score(event) {
    // let score = event.target.value.toUpperCase()
    // if (!is_score_valid(score)) {
    //     alert(`Invalid score ${score}`);
    //     event.target.value = null;
    //     return;
    // }
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
    if (score == 'M' || score == 'X') {
        return true;
    }
    if (score > 0 && score <=10 ) {
        return true;
    }
    return false;
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