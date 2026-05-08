*** Settings ***
Library    Vibium    headless=${HEADLESS}
Library    OperatingSystem

*** Variables ***
${BASE_URL}    https://example.com
${HEADLESS}    ${TRUE}

*** Keywords ***
Open Test Browser
    Open Browser

Close Test Browser
    Close Browser

Go To Blank Page
    Go To    about:blank

Reset Interaction Fixture
    Go To    data:text/html,<main><input id='name'/><button id='save' data-clicked='0' onclick="this.setAttribute('data-clicked',String(Number(this.getAttribute('data-clicked'))+1))">Save</button></main>

Reset Frame Fixture
    Go To    data:text/html,<main><iframe name='child' srcdoc="<input id='in-frame' value='start' /><p id='status'>inside-frame</p>"></iframe></main>

Reset Wait Fixture
    Go To    data:text/html,<main><div id='status'>ready</div></main>

Reset Mouse Fixture
    Go To    data:text/html,<main><button id='mouse-btn' data-pressed='0'>Mouse Target</button></main>

Reset Deferred Visible Fixture
    Go To    data:text/html,<main><div id='box' style='display:none'>ready</div><script>setTimeout(function(){document.getElementById('box').style.display='block';},400);</script></main>

Trigger Alert Dialog
    Evaluate JavaScript    () => { alert('hello'); return true; }

Trigger Confirm Dialog
    Evaluate JavaScript    () => { confirm('continue?'); return true; }
