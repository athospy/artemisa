let status = 'preparing';
let interval = null;
document.addEventListener('DOMContentLoaded', function() {
    document.querySelector('#start_button').addEventListener('click', start_preparing_timer);
    document.querySelector('#stop_button').addEventListener('click', stop_timer);
});

async function start_preparing_timer() {
    document.querySelector('#clock').style.display = "block";
    document.querySelector('#start_button').style.display = "none";
    document.querySelector('#stop_button').style.display = "block";
    await beep();
    await beep();
    countdown('clock', 0, 10);
}

async function start_competition_timer() {
    await beep();
    countdown('clock', 0, 15);
}

async function finish_timer() {
    await beep();
    await beep();
    await beep();
    document.querySelector('#clock').innerHTML = "";
    document.querySelector('#clock').style.display = "none";
    document.querySelector('#start_button').style.display = "block";
    document.querySelector('#stop_button').style.display = "none";
}

async function stop_timer() {
    clearInterval(interval);
    finish_timer();
}

function countdown(element, minutes, seconds) {
    // set time for the particular countdown
    var time = minutes*60 + seconds;
    interval = setInterval(function() {
        var el = document.getElementById(element);
        // if the time is 0 then end the counter
        if (time <= 0) {
            if (status ==  'preparing') {
                clearInterval(interval);
                start_competition_timer();
                status = 'competing';
                return;
            }
            if (status ==  'competing') {
                clearInterval(interval);
                var text = "time's up";
                el.innerHTML = text;
                status = 'preparing';
                finish_timer();
                return;
            }
        }
        if (time == 10 && status ==  'competing') {
            warning();
        }
        var minutes = Math.floor( time / 60 );
        if (minutes < 10) minutes = "0" + minutes;
        var seconds = time % 60;
        if (seconds < 10) seconds = "0" + seconds;
        var text = minutes + ':' + seconds;
        el.innerHTML = text;
        time--;
    }, 1000);
}

// makes playing audio return a promise
function playAudio(audio){
    return new Promise(res=>{
        audio.currentTime = 0; // Reset the audio to the start
        audio.play()
        audio.onended = res
    })
  }


async function beep(){
    // const audio = new Audio("{{ static '/artemisa/whistle.wav' }}")
    const audio = document.getElementById('beep_audio');
    // console.log(audio);
    await playAudio(audio)
    // code that will run after audio finishes...
}

async function warning(){
    // const audio = new Audio("{{ static '/artemisa/whistle.wav' }}")
    const audio = document.getElementById('warning_audio');
    // console.log(audio);
    await playAudio(audio)
    // code that will run after audio finishes...
}

