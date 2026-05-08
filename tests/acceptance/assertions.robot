*** Settings ***
Resource    resources/common.resource
Suite Setup    Open Test Browser
Suite Teardown    Close Test Browser

*** Test Cases ***
Evaluate JavaScript Returns Value
    [Documentation]    Validates page.evaluate plumbed through the library.
    [Tags]    acceptance    assertions    core
    Go To Blank Page
    ${n}=    Evaluate JavaScript    40+1
    Should Be Equal As Numbers    ${n}    ${41}

Get Title Reads Embedded Title
    [Documentation]    Validates document title retrieval on a data URL shell.
    [Tags]    acceptance    assertions
    Go To    data:text/html,<html><head><title>vibium-e2e-title</title></head><body>ok</body></html>
    ${title}=    Get Title
    Should Be Equal    ${title}    vibium-e2e-title

Count Elements On Static Page
    [Documentation]    Validates Count Elements locator resolution.
    [Tags]    acceptance    assertions
    Go To    data:text/html,<main><p>one</p><p>two</p></main>
    ${c}=    Count Elements    css:p
    Should Be Equal As Integers    ${c}    ${2}
