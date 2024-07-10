document.addEventListener('DOMContentLoaded', function() {
    const select_category = document.querySelector('#select_category');
    // select_category.addEventListener('change', select_category);

    select_category.addEventListener('change', function(event) {
        console.log('Selected category changed to:', event.target.value);
        const category_id = document.querySelector('#select_category').value;
        fetch(`/result_category`, {
            method: 'POST',
            body: JSON.stringify({
                category_id: category_id,
            })
        })
        .then(response => response.json())
        .then(result => {
            const result_container = document.querySelector('#result_container');
            result_container.innerHTML = '';
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
                    `<div class="row justify-content-between mt-4">
                        <h1 class="col-1">${counter}</h1>
                        <h1 class="col-9">${archer.name}</h1>
                        <h1 class="col-2">${archer.score}</h1>
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

function select_category() {
    const category_id = document.querySelector('#select_category').value;
    fetch(`/result_category`, {
        method: 'POST',
        body: JSON.stringify({
            category_id: category_id,
        })
    })
    .then(response => response.json())
    .then(result => {
        const result_container = document.querySelector('#result_container');
        result_container.innerHTML = '';
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
                `<div class="row justify-content-between mt-4">
                    <h1 class="col-1">${counter}</h1>
                    <h1 class="col-9">${archer.name}</h1>
                    <h1 class="col-2">${archer.score}</h1>
                </div>`
            );
        });

    })
    .catch(error => {
        console.log(error)
    });
}
