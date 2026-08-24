*** Settings ***
Resource    resources/common.resource
Suite Teardown    Close All Browsers

*** Test Cases ***
Default Open Browser Uses Chrome
    [Documentation]    ``Open Browser`` without ``engine=`` launches Chrome unless ``VIBIUM_ENGINE`` is set.
    [Tags]    acceptance    engine    core
    Open Browser
    Go To Blank Page
    ${ua}=    Evaluate JavaScript    navigator.userAgent
    Should Contain    ${ua}    Chrome
    Should Not Contain    ${ua}    Firefox
    Close Browser

Open Browser With Firefox Engine
    [Documentation]    ``engine=firefox`` launches Firefox (requires ``vibium install --engine firefox``).
    [Tags]    acceptance    engine    firefox
    Open Browser    engine=firefox
    Go To Blank Page
    ${ua}=    Evaluate JavaScript    navigator.userAgent
    Should Contain    ${ua}    Firefox
    Close Browser
