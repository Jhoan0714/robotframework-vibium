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
