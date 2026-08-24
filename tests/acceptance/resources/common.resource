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

Reset Keyboard Fixture
    [Documentation]    Input plus Enter handler for page-level and element keystrokes.
    Set Page Content    <html><body><input id="name"/><input id="q"/><p id="out"></p><script>document.getElementById("q").addEventListener("keydown",function(e){if(e.key==="Enter")document.getElementById("out").textContent="enter";});</script></body></html>

Reset Deferred Visible Fixture
    Go To    data:text/html,<main><div id='box' style='display:none'>ready</div><script>setTimeout(function(){document.getElementById('box').style.display='block';},400);</script></main>

Reset Pierce Fixture
    [Documentation]    Open-shadow Web Components for pierce combinators (``>>`` / ``>>>``).
    Go To    data:text/html,<main><my-card></my-card><outer-host></outer-host></main><script>customElements.define('my-card',class extends HTMLElement{connectedCallback(){const r=this.attachShadow({mode:'open'});r.innerHTML="<p id='shadow-text'>inside shadow</p><button id='shadow-btn' data-clicked='0'>Save</button>";r.getElementById('shadow-btn').addEventListener('click',function(){this.setAttribute('data-clicked',String(Number(this.getAttribute('data-clicked'))+1));});}});customElements.define('inner-host',class extends HTMLElement{connectedCallback(){this.attachShadow({mode:'open'}).innerHTML="<p id='deep'>nested shadow</p>";}});customElements.define('outer-host',class extends HTMLElement{connectedCallback(){this.attachShadow({mode:'open'}).innerHTML='<inner-host></inner-host>';}});</script>

Trigger Alert Dialog
    Evaluate JavaScript    () => { alert('hello'); return true; }

Trigger Confirm Dialog
    Evaluate JavaScript    () => { confirm('continue?'); return true; }
