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
        divs.forEach(el => el.addEventListener('blur', add_score));
    })
    .catch(error => {
        console.log(error)
    });
}

// check valid and loop for every 6 inputs for adding the score and check if is and 'x' or a '10' for adding in each score respectively
// loop through each input every time for preventing error when editing scores
// transforming de 'X' to 10 and the 'M' to 0 for the scoring
function add_score(event) {
    let score = event.target.value.toUpperCase()
    if (!is_score_valid(score)) {
        alert(`Invalid score ${score}`);
        event.target.value = null;
        return;
    }
    const end_number = event.target.dataset.end;
    const shoot_number = event.target.dataset.shoot;
    const archer_id = event.target.dataset.archer_id;
    init_zero_end(end_number, archer_id);
    const shoots_scores = document.querySelectorAll(`#archer_${archer_id} .shoot_input`);
    let all_scores_input_filled = true;
    let shoot_array = [];
    shoots_scores.forEach(el => {
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
        const userConfirmed = confirm("Are you sure you want to proceed?");
        // Check the user's response
        if (!userConfirmed) {
            return;
        }
        save_score_db(shoot_array, archer_id, end_number);
        shoots_scores.forEach(el => {
            el.disabled = "disabled";
            el.classList.remove("shoot_input");
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
    }
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
