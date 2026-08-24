*** Settings ***
Resource    resources/common.resource
Suite Setup    Open Test Browser
Suite Teardown    Close Test Browser

*** Test Cases ***
Set And Get Viewport Size
    [Documentation]    Viewport size round-trip on the active page.
    [Tags]    acceptance    emulation
    Go To Blank Page
    Set Viewport Size    800    600
    ${size}=    Get Viewport Size
    Should Be Equal As Integers    ${size}[width]    800
    Should Be Equal As Integers    ${size}[height]    600

Set And Get Window Info
    [Documentation]    OS window size is applied; Get Window Info returns dimensions.
    [Tags]    acceptance    emulation
    Go To Blank Page
    Set Window    width=1024    height=768
    ${info}=    Get Window Info
    Should Be Equal As Integers    ${info}[width]    1024
    Should Be Equal As Integers    ${info}[height]    768

Set Window State
    [Documentation]    Window state is applied and visible in Get Window Info.
    [Tags]    acceptance    emulation
    Go To Blank Page
    Set Window    state=normal
    ${info}=    Get Window Info
    Should Be Equal    ${info}[state]    normal
