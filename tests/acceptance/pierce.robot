*** Settings ***
Resource    resources/common.resource
Suite Setup    Open Test Browser
Suite Teardown    Close Test Browser
Test Setup    Reset Pierce Fixture

*** Test Cases ***
Get Text Via Single Pierce
    [Documentation]    Reads text inside an open shadow root with ``>>``.
    [Tags]    acceptance    pierce    core
    ${text}=    Get Text    my-card >> #shadow-text
    Should Be Equal    ${text}    inside shadow

Click Via Single Pierce
    [Documentation]    Clicks a button inside an open shadow root with ``>>``.
    [Tags]    acceptance    pierce
    Click    my-card >> #shadow-btn
    ${clicked}=    Get Attribute    data-clicked    my-card >> #shadow-btn
    Should Be Equal    ${clicked}    1

Get Text Via Deep Pierce
    [Documentation]    Reads text across nested open shadow roots with ``>>>``.
    [Tags]    acceptance    pierce
    ${text}=    Get Text    outer-host >>> #deep
    Should Be Equal    ${text}    nested shadow

Plain Css Selector Does Not Reach Shadow Content
    [Documentation]    Shadow-only ids are not visible to light-DOM ``css:`` selectors; pierce is required.
    [Tags]    acceptance    pierce    negative
    Run Keyword And Expect Error    *element not found*    Get Text    css:#shadow-text

Single Pierce Does Not Reach Nested Shadow
    [Documentation]    ``>>`` crosses one shadow boundary; ``#deep`` lives two levels below ``outer-host``.
    [Tags]    acceptance    pierce    negative
    Run Keyword And Expect Error    *element not found*    Get Text    outer-host >> #deep
