*** Settings ***
Resource    resources/common.resource
Suite Setup    Open Test Browser
Suite Teardown    Close Test Browser
Test Setup    Reset Wait Fixture

*** Test Cases ***
Wait For Text Finds Existing Content
    [Documentation]    Validates Wait For Text on already-present text.
    [Tags]    acceptance    waits    core
    Wait For Text    ready    timeout=2s
    ${text}=    Get Page Text
    Should Contain    ${text}    ready

Wait For Url Matches About Blank
    [Documentation]    Validates Wait For Url behavior.
    [Tags]    acceptance    waits
    Go To Blank Page
    Wait For Url    about:blank    timeout=2s
    ${url}=    Get Url
    Should Be Equal    ${url}    about:blank

Wait For Function Ready State
    [Documentation]    Validates Wait For Function execution path.
    [Tags]    acceptance    waits
    Wait For Function    () => document.readyState === 'complete'    timeout=2s

Wait For Load State On Static Page
    [Documentation]    Validates Wait For Load State against ``document.readyState`` ``complete``.
    [Tags]    acceptance    waits    core
    Go To    data:text/html,<p id='x'>load-e2e</p>
    Wait For Load State    complete    timeout=10s
    Wait For Element    css:#x    state=visible    timeout=10s

Wait For Deferred Visible Element
    [Documentation]    Validates Wait For Element when content appears after a timeout.
    [Tags]    acceptance    waits    core
    Reset Deferred Visible Fixture
    Wait For Element    css:#box    state=visible    timeout=5s
    ${txt}=    Get Element Text    css:#box
    Should Be Equal    ${txt}    ready
