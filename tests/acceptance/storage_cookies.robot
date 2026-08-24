*** Settings ***
Resource    resources/common.resource
Suite Setup    Open Test Browser
Suite Teardown    Close Test Browser

*** Test Cases ***
Set List And Clear Cookies
    [Documentation]    Validates cookie lifecycle keywords in active context.
    [Tags]    acceptance    cookies    core
    Go To    ${BASE_URL}
    Set Cookie    rf_acceptance    one    url=${BASE_URL}
    ${cookies}=    List Cookies
    ${cookie_names}=    Evaluate    [c["name"] for c in $cookies]
    Should Contain    ${cookie_names}    rf_acceptance
    Clear Cookies
    ${after_clear}=    List Cookies
    ${count}=    Get Length    ${after_clear}
    Should Be Equal As Integers    ${count}    0

Export And Restore Storage State
    [Documentation]    Validates storage state export and restore workflow.
    [Tags]    acceptance    storage
    Go To    ${BASE_URL}
    Set Cookie    rf_state_cookie    restored    url=${BASE_URL}    same_site=lax
    ${path}=    Export Storage State    output_path=acceptance/storage-state.json    embed=${FALSE}
    File Should Exist    ${path}
    Clear Cookies
    Restore Storage State    ${path}
    ${cookies}=    List Cookies
    ${cookie_names}=    Evaluate    [c["name"] for c in $cookies]
    Should Contain    ${cookie_names}    rf_state_cookie

Clear Storage Removes Origin Data
    [Documentation]    Clears localStorage on the current origin.
    [Tags]    acceptance    storage
    Go To    ${BASE_URL}
    ${before}=    Evaluate JavaScript    localStorage.setItem('rf_clear', '1'), localStorage.getItem('rf_clear')
    Should Be Equal    ${before}    1
    Clear Storage
    ${after}=    Evaluate JavaScript    localStorage.getItem('rf_clear')
    Should Be Equal    ${after}    ${NONE}
