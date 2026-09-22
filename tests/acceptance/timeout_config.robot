*** Settings ***
Resource    resources/common.resource
Suite Setup    Open Test Browser
Suite Teardown    Reset Library Timeout And Close Browser
Test Setup    Reset Interaction Fixture

*** Keywords ***
Reset Library Timeout And Close Browser
    [Documentation]    Clear any Global timeout override left by this suite, then close the browser.
    Set Browser Timeout    None    scope=Global
    Close Test Browser

*** Test Cases ***
Per Call Timeout Overrides Library Default
    [Documentation]    Explicit timeout= on find/action wins over Set Browser Timeout (hierarchy).
    [Tags]    acceptance    config
    Set Browser Timeout    30s    scope=Test
    Run Keyword And Expect Error    *element not found*
    ...    Find Element    css:#no-such-element    timeout=500ms
    Run Keyword And Expect Error    *element not found*
    ...    Click    css:#no-such-click    timeout=500ms

Test Scope Applies When Timeout Omitted
    [Documentation]    Test-scoped library default is used when the keyword omits timeout=.
    [Tags]    acceptance    config
    Set Browser Timeout    500ms    scope=Test
    Run Keyword And Expect Error    *element not found*    Find Element    css:#no-such-test-scope
    # Intentionally no restore — end_test listener must clear before the next test.

Test Scope Cleared When Previous Test Ends
    [Documentation]    Listener end_test restores the prior value (here: no override).
    [Tags]    acceptance    config
    ${old}=    Set Browser Timeout    1s    scope=Test
    Should Be Equal    ${old}    None
    Set Browser Timeout    ${old}    scope=Test

Default Scope Is Suite
    [Documentation]    Omitting scope= uses Suite (default).
    [Tags]    acceptance    config
    Set Browser Timeout    500ms
    Run Keyword And Expect Error    *element not found*    Find Element    css:#no-such-default-suite

Suite Scope Still Active In Following Test
    [Documentation]    Suite-scoped timeout from the previous test still applies (same suite).
    [Tags]    acceptance    config
    Run Keyword And Expect Error    *element not found*    Find Element    css:#no-such-suite-persist
    Set Browser Timeout    None    scope=Suite

Global Scope Applies When Timeout Omitted
    [Documentation]    Global-scoped library default is used when the keyword omits timeout=.
    [Tags]    acceptance    config
    Set Browser Timeout    500ms    scope=Global
    Run Keyword And Expect Error    *element not found*    Find Element    css:#no-such-global

Global Scope Persists To Following Test
    [Documentation]    Global timeout remains until cleared or overwritten (library is GLOBAL).
    [Tags]    acceptance    config
    Run Keyword And Expect Error    *element not found*    Find Element    css:#no-such-global-persist
    Set Browser Timeout    None    scope=Global

Library Timeout Applies To Action Keywords
    [Documentation]    Set Browser Timeout is used by actions (Click) when timeout= is omitted.
    [Tags]    acceptance    config
    Set Browser Timeout    500ms    scope=Test
    Run Keyword And Expect Error    *element not found*    Click    css:#no-such-click
