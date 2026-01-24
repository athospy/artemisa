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
    const select_category = document.querySelector('#select_category');
    const headerRow = `<div class="row font-weight-bold">
        <div class="col-1">#</div>
        <div class="col-5">Archer</div>
        <div class="col-2 text-center">Score</div>
        <div class="col-1 text-center">10s</div>
        <div class="col-1 text-center">Xs</div>
        <div class="col-2 text-center">Last End</div>
    </div>`;
    // select_category.addEventListener('change', select_category);

    select_category.addEventListener('change', function(event) {
        console.log('Selected category changed to:', event.target.value);
        const category_id = document.querySelector('#select_category').value;
        fetch(`/result_category`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': csrfToken,
            },
            body: JSON.stringify({
                category_id: category_id,
            })
        })
        .then(response => response.json())
        .then(result => {
            const result_container = document.querySelector('#result_container');
            result_container.innerHTML = headerRow;
            // console.log(result);
            // Parse the JSON string to get the array
            const archerList = JSON.parse(result.data);

            // Loop through the array and access each object
            let counter = 0;
            archerList.forEach(archer => {
                counter ++;
                // console.log(`Name: ${archer.name}, Score: ${archer.score}`);
                result_container.insertAdjacentHTML(
                    'beforeend',
                    `<div class="row justify-content-between mt-4 align-items-center">
                        <h3 class="col-1">${counter}</h3>
                        <h3 class="col-5">${archer.name}</h3>
                        <h3 class="col-2 text-center">${archer.score}</h3>
                        <h4 class="col-1 text-center">${archer.tens}</h4>
                        <h4 class="col-1 text-center">${archer.xs}</h4>
                        <h4 class="col-2 text-center">${archer.last_end_total}</h4>
                    </div>`
                );
            });

        })
        .catch(error => {
            console.log(error)
        });
    });


    const options = select_category.options;
    let index = 1;

    function changeDropdownValue() {
        if (index < options.length) {
            select_category.selectedIndex = index;
            select_category.dispatchEvent(new Event('change')); // Trigger change event
            index++;
        } else {
            index = 1; // Reset to the first option after the last one
            select_category.selectedIndex = index;
            select_category.dispatchEvent(new Event('change')); // Trigger change event
            index++;
        }
    }
    setInterval(changeDropdownValue, 3000); // Change value every 5 seconds
});

