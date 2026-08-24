*** Settings ***
Resource    resources/common.resource

Suite Teardown    Close All Browsers

*** Test Cases ***
Two Independent Browsers Active And Scoped Url
    [Documentation]
    ...    Validates a second browser becoming active while the first stays addressable via
    ...    ``Get Active Page    browser=${handle}`` and ``Get Url    scope=${page}``.
    [Tags]    acceptance    multi-browser    core
    ${b1}=    Open Browser
    Go To    ${BASE_URL}
    ${p1}=    Get Active Page    browser=${b1}
    ${b2}=    Open Browser
    Go To Blank Page
    ${url_active}=    Get Url
    Should Be Equal    ${url_active}    about:blank
    ${url_first}=    Get Url    scope=${p1}
    Should Contain    ${url_first}    example.com

Chrome And Firefox Independent Sessions
    [Documentation]
    ...    Same multi-browser scoping as above, with the second session on Firefox.
    ...    Requires ``vibium install --engine firefox``.
    [Tags]    acceptance    multi-browser    engine    firefox
    ${chrome}=    Open Browser
    Go To    ${BASE_URL}
    ${p_chrome}=    Get Active Page    browser=${chrome}

    ${firefox}=    Open Browser    engine=firefox
    Go To Blank Page
    ${ua_firefox}=    Evaluate JavaScript    navigator.userAgent
    Should Contain    ${ua_firefox}    Firefox

    ${url_active}=    Get Url
    Should Be Equal    ${url_active}    about:blank

    ${url_chrome}=    Get Url    scope=${p_chrome}
    Should Contain    ${url_chrome}    example.com
    ${ua_chrome}=    Evaluate JavaScript    navigator.userAgent    scope=${p_chrome}
    Should Contain    ${ua_chrome}    Chrome
    Should Not Contain    ${ua_chrome}    Firefox
