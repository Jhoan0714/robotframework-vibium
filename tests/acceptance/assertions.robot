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

Get Title Inline Assertion
    [Documentation]    AssertionEngine on Get Title (#18).
    [Tags]    acceptance    assertions    assertionengine
    Go To    data:text/html,<html><head><title>vibium-e2e-title</title></head><body>ok</body></html>
    ${title}=    Get Title    ==    vibium-e2e-title
    Should Be Equal    ${title}    vibium-e2e-title
    Run Keyword And Expect Error    *    Get Title    ==    wrong-title

Count Elements On Static Page
    [Documentation]    Validates Count Elements locator resolution.
    [Tags]    acceptance    assertions
    Go To    data:text/html,<main><p>one</p><p>two</p></main>
    ${c}=    Count Elements    css:p
    Should Be Equal As Integers    ${c}    ${2}

Count Elements Inline Assertion
    [Documentation]    AssertionEngine peel on Count Elements (#18).
    [Tags]    acceptance    assertions    assertionengine
    Go To    data:text/html,<main><p>one</p><p>two</p></main>
    Count Elements    css:p    ==    ${2}

Get Text Inline Assertion
    [Documentation]    AssertionEngine peel on Get Text with locator (#18).
    [Tags]    acceptance    assertions    assertionengine
    Go To    data:text/html,<main><h1 id="t">Welcome</h1></main>
    Get Text    css:#t    ==    Welcome
    ${text}=    Get Text    css:#t    contains    Wel
    Should Be Equal    ${text}    Welcome

Get Element States Lists Active States
    [Documentation]    Additive Get Element States (#18).
    [Tags]    acceptance    assertions    assertionengine
    Go To    data:text/html,<main><button id="b">Go</button></main>
    @{states}=    Get Element States    css:#b
    Should Contain    ${states}    visible
    Get Element States    css:#b    *=    visible

Get Text Inline Assertion With Scope Timeout Message
    [Documentation]    AssertionEngine with named scope=, timeout=, and message= (#18).
    [Tags]    acceptance    assertions    assertionengine
    Reset Frame Fixture
    ${frame}=    Get Frame    child
    ${text}=    Get Text    css:#status    ==    inside-frame    scope=${frame}    timeout=5s
    Should Be Equal    ${text}    inside-frame
    Run Keyword And Expect Error    custom-assert-msg
    ...    Get Text    css:#status    ==    wrong    scope=${frame}    timeout=5s    message=custom-assert-msg

Get Text Inline Assertion Timeout Expires
    [Documentation]    timeout= on find fails fast when the element is missing; assert is not reached (#18).
    [Tags]    acceptance    assertions    assertionengine
    Go To Blank Page
    Run Keyword And Expect Error    *element not found*
    ...    Get Text    css:#no-such    ==    x    timeout=500ms    message=should-not-reach-assert
