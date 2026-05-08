*** Settings ***
Resource    resources/common.resource
Suite Setup    Open Test Browser
Suite Teardown    Close Test Browser
Test Setup    Reset Frame Fixture

*** Test Cases ***
Get Frame And Read Content
    [Documentation]    Resolves a frame by name and reads content using explicit scope.
    [Tags]    acceptance    frames    core
    ${frame}=    Get Frame    child
    ${text}=    Get Element Text    css:#status    scope=${frame}
    Should Be Equal    ${text}    inside-frame

Fill Element Inside Frame
    [Documentation]    Fills an input inside a frame using object-first scope.
    [Tags]    acceptance    frames
    ${frame}=    Get Frame    child
    Fill Element    css:#in-frame    in-frame-value    scope=${frame}
    ${value}=    Get Element Value    css:#in-frame    scope=${frame}
    Should Be Equal    ${value}    in-frame-value
