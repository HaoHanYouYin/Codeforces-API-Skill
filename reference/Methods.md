
Methods
=======

### blogEntry.comments

Returns a list of comments to the specified blog entry.

| Parameter                        | Description                                                                                                   |
| -------------------------------- | ------------------------------------------------------------------------------------------------------------- |
| **blogEntryId** (Required) | Id of the blog entry. It can be seen in blog entry URL. For example:[/blog/entry/**79**](/blog/entry/79) |

**Return value**: A list of [Comment](/apiHelp/objects#Comment) objects.

**Example**: [https://codeforces.com/api/blogEntry.comments?blogEntryId=79](https://codeforces.com/api/blogEntry.comments?blogEntryId=79)

### blogEntry.view

Returns blog entry.

| Parameter                        | Description                                                                                                   |
| -------------------------------- | ------------------------------------------------------------------------------------------------------------- |
| **blogEntryId** (Required) | Id of the blog entry. It can be seen in blog entry URL. For example:[/blog/entry/**79**](/blog/entry/79) |

**Return value**: Returns a [BlogEntry](/apiHelp/objects#BlogEntry) object in full version.

**Example**: [https://codeforces.com/api/blogEntry.view?blogEntryId=79](https://codeforces.com/api/blogEntry.view?blogEntryId=79)

### contest.hacks

Returns list of hacks in the specified contests. Full information about hacks is available only after some time after the contest end. During the contest user can see only own hacks.

| Parameter                      | Description                                                                                                                                                                                                                     |
| ------------------------------ | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| **contestId** (Required) | Id of the contest. It is**not** the round number. It can be seen in contest URL. For example: [/contest/**566**/status](/contest/566/status)                                                                         |
| **asManager**            | Boolean. If set to true, the response will contain information available to contest managers. Otherwise, the response will contain only the information available to the participants. You must be a contest manager to use it. |

**Return value**: Returns a list of [Hack](/apiHelp/objects#Hack) objects.

**Example**: [https://codeforces.com/api/contest.hacks?contestId=566](https://codeforces.com/api/contest.hacks?contestId=566)

### contest.list

Returns information about all available contests.

| Parameter           | Description                                                                                                                                 |
| ------------------- | ------------------------------------------------------------------------------------------------------------------------------------------- |
| **gym**       | Boolean. If true — than gym contests are returned. Otherwide, regular contests are returned.                                               |
| **groupCode** | Group code (e.g.,`sfSJn5pz1a`) is used to filter contests. You need to log in with an account that has at least read access to the group. |

**Return value**: Returns a list of [Contest](/apiHelp/objects#Contest) objects. If this method is called not anonymously, then all available contests for a calling user will be returned too, including mashups and private gyms.

**Example**: [https://codeforces.com/api/contest.list?gym=true](https://codeforces.com/api/contest.list?gym=true)

### contest.ratingChanges

Returns rating changes after the contest.

| Parameter                      | Description                                                                                                                                             |
| ------------------------------ | ------------------------------------------------------------------------------------------------------------------------------------------------------- |
| **contestId** (Required) | Id of the contest. It is**not** the round number. It can be seen in contest URL. For example: [/contest/**566**/status](/contest/566/status) |

**Return value**: Returns a list of [RatingChange](/apiHelp/objects#RatingChange) objects.

**Example**: [https://codeforces.com/api/contest.ratingChanges?contestId=566](https://codeforces.com/api/contest.ratingChanges?contestId=566)

### contest.standings

Returns the contest description and standings.

For gym and mashup contests, this method is available only through an authenticated API request from a user who can view the contest. Optional parameters may be used to page or filter the returned standings.

For regular contests, ordinary and anonymous users can request standings only for public contests, and only by an anonymous GET request with exactly one query parameter: `contestId`. Use `https://codeforces.com/api/contest.standings?contestId=<id>`.

In this regular contest mode, the response contains the full official public standings only. Do not specify `from`, `count`, `handles`, `room`, `showUnofficial`, `participantTypes`, API authentication parameters, or any other parameters. Non-public regular contests and regular contests with hidden standings are not available through this public mode.

| Parameter                      | Description                                                                                                                                                                                                                     |
| ------------------------------ | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| **contestId** (Required) | Id of the contest. It is**not** the round number. It can be seen in contest URL. For example: [/contest/**566**/status](/contest/566/status)                                                                         |
| **asManager**            | Boolean. If set to true, the response will contain information available to contest managers. Otherwise, the response will contain only the information available to the participants. You must be a contest manager to use it. |
| **from**                 | 1-based index of the standings row to start the ranklist.                                                                                                                                                                       |
| **count**                | Number of standing rows to return.                                                                                                                                                                                              |
| **handles**              | Semicolon-separated list of handles. No more than 10000 handles is accepted.                                                                                                                                                    |
| **room**                 | If specified, than only participants from this room will be shown in the result. If not — all the participants will be shown.                                                                                                  |
| **showUnofficial**       | If true than all participants (virtual, out of competition) are shown. Otherwise, only official contestants are shown.                                                                                                          |
| **participantTypes**     | Comma-separated list of participant types without spaces. Possible values: CONTESTANT, PRACTICE, VIRTUAL, MANAGER, OUT\_OF\_COMPETITION. Only participants with the specified types will be displayed.                          |

**Return value**: Returns object with three fields: "contest", "problems" and "rows". Field "contest" contains a [Contest](/apiHelp/objects#Contest) object. Field "problems" contains a list of [Problem](/apiHelp/objects#Problem) objects. Field "rows" contains a list of [RanklistRow](/apiHelp/objects#RanklistRow) objects.

**Example**: [https://codeforces.com/api/contest.standings?contestId=566](https://codeforces.com/api/contest.standings?contestId=566)

### contest.status

Returns submissions for specified contest. Optionally can return submissions of specified user.

| Parameter                      | Description                                                                                                                                                                                                                     |
| ------------------------------ | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| **contestId** (Required) | Id of the contest. It is**not** the round number. It can be seen in contest URL. For example: [/contest/**566**/status](/contest/566/status)                                                                         |
| **asManager**            | Boolean. If set to true, the response will contain information available to contest managers. Otherwise, the response will contain only the information available to the participants. You must be a contest manager to use it. |
| **handle**               | Codeforces user handle.                                                                                                                                                                                                         |
| **from**                 | 1-based index of the first submission to return.                                                                                                                                                                                |
| **count**                | Number of returned submissions.                                                                                                                                                                                                 |
| **includeSources**       | Specifies whether to include source codes in the output. Available only when using asManager and if the user has manager permissions for the contest.                                                                           |

**Return value**: Returns a list of [Submission](/apiHelp/objects#Submission) objects, sorted in decreasing order of submission id.

**Example**: [https://codeforces.com/api/contest.status?contestId=566&amp;from=1&amp;count=10](https://codeforces.com/api/contest.status?contestId=566&from=1&count=10)

### group.isManager

Returns whether the specified users are managers of the given group. This method is available only to authorized API users.

| Parameter                      | Description                                                                  |
| ------------------------------ | ---------------------------------------------------------------------------- |
| **groupCode** (Required) | Group code.                                                                  |
| **handles** (Required)   | Semicolon-separated list of handles. No more than 10000 handles is accepted. |

**Return value**: A map from user handles to boolean values indicating whether each user is a manager of the group.

**Example**: [https://codeforces.com/api/group.isManager?groupCode=JMRDZdAtYr&amp;handles=MikeMirzayanov;tourist](https://codeforces.com/api/group.isManager?groupCode=JMRDZdAtYr&handles=MikeMirzayanov;tourist)

### problemset.problems

Returns all problems from problemset. Problems can be filtered by tags.

| Parameter                | Description                                     |
| ------------------------ | ----------------------------------------------- |
| **tags**           | Semicilon-separated list of tags.               |
| **problemsetName** | Custom problemset's short name, like 'acmsguru' |

**Return value**: Returns two lists. List of [Problem](/apiHelp/objects#Problem) objects and list of [ProblemStatistics](/apiHelp/objects#ProblemStatistics) objects.

**Example**: [https://codeforces.com/api/problemset.problems?tags=implementation](https://codeforces.com/api/problemset.problems?tags=implementation)

### problemset.recentStatus

Returns recent submissions.

| Parameter                  | Description                                         |
| -------------------------- | --------------------------------------------------- |
| **count** (Required) | Number of submissions to return. Can be up to 1000. |
| **problemsetName**   | Custom problemset's short name, like 'acmsguru'     |

**Return value**: Returns a list of [Submission](/apiHelp/objects#Submission) objects, sorted in decreasing order of submission id.

**Example**: [https://codeforces.com/api/problemset.recentStatus?count=10](https://codeforces.com/api/problemset.recentStatus?count=10)

### recentActions

Returns recent actions.

| Parameter                     | Description                                           |
| ----------------------------- | ----------------------------------------------------- |
| **maxCount** (Required) | Number of recent actions to return. Can be up to 100. |

**Return value**: Returns a list of [RecentAction](/apiHelp/objects#RecentAction) objects.

**Example**: [https://codeforces.com/api/recentActions?maxCount=30](https://codeforces.com/api/recentActions?maxCount=30)

### system.status

The system.status method provides a real-time health check (Health Check) of the system’s core infrastructure and processing pipeline. It returns the current availability status of internal services and key performance metrics (throughput) from the last 5 minutes.

| Parameter | Description |
| --------- | ----------- |

**Return value**: Returns a JSON object representing the real-time health status of core infrastructure components and system throughput metrics for the last 5 minutes.

**Example**: [https://codeforces.com/api/system.status](https://codeforces.com/api/system.status)

### user.blogEntries

Returns a list of all user's blog entries.

| Parameter                   | Description             |
| --------------------------- | ----------------------- |
| **handle** (Required) | Codeforces user handle. |

**Return value**: A list of [BlogEntry](/apiHelp/objects#BlogEntry) objects in short form.

**Example**: [https://codeforces.com/api/user.blogEntries?handle=Fefer\_Ivan](https://codeforces.com/api/user.blogEntries?handle=Fefer_Ivan)

### user.friends

Returns authorized user's friends. Using this method requires authorization.

| Parameter            | Description                                                                                |
| -------------------- | ------------------------------------------------------------------------------------------ |
| **onlyOnline** | Boolean. If true — only online friends are returned. Otherwise, all friends are returned. |

**Return value**: Returns a list of strings — users' handles.

**Example**: [https://codeforces.com/api/user.friends?onlyOnline=true](https://codeforces.com/api/user.friends?onlyOnline=true)

### user.info

Returns information about one or several users.

| Parameter                      | Description                                                                                                                    |
| ------------------------------ | ------------------------------------------------------------------------------------------------------------------------------ |
| **handles** (Required)   | Semicolon-separated list of handles. No more than 10000 handles is accepted.                                                   |
| **checkHistoricHandles** | Boolean, the default value is true. If this flag is enabled, then use the history of handle changes when searching for a user. |

**Return value**: Returns a list of [User](/apiHelp/objects#User) objects for requested handles, in same order as in parameters.

**Example**: [https://codeforces.com/api/user.info?handles=DmitriyH;Fefer\_Ivan&amp;checkHistoricHandles=false](https://codeforces.com/api/user.info?handles=DmitriyH;Fefer_Ivan&checkHistoricHandles=false)

### user.ratedList

Returns the list users who have participated in at least one rated contest.

| Parameter                | Description                                                                                                                                                                |
| ------------------------ | -------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| **activeOnly**     | Boolean. If true then only users, who participated in rated contest during the last month are returned. Otherwise, all users with at least one rated contest are returned. |
| **includeRetired** | Boolean. If true, the method returns all rated users, otherwise the method returns only users, that were online at last month.                                             |
| **contestId**      | Id of the contest. It is**not** the round number. It can be seen in contest URL. For example: [/contest/**566**/status](/contest/566/status)                    |

**Return value**: Returns a list of [User](/apiHelp/objects#User) objects, sorted in decreasing order of rating.

**Example**: [https://codeforces.com/api/user.ratedList?activeOnly=true&amp;includeRetired=false](https://codeforces.com/api/user.ratedList?activeOnly=true&includeRetired=false)

### user.rating

Returns rating history of the specified user.

| Parameter                   | Description             |
| --------------------------- | ----------------------- |
| **handle** (Required) | Codeforces user handle. |

**Return value**: Returns a list of [RatingChange](/apiHelp/objects#RatingChange) objects for requested user.

**Example**: [https://codeforces.com/api/user.rating?handle=Fefer\_Ivan](https://codeforces.com/api/user.rating?handle=Fefer_Ivan)

### user.status

Returns submissions of specified user.

| Parameter                   | Description                                                                                                                         |
| --------------------------- | ----------------------------------------------------------------------------------------------------------------------------------- |
| **handle** (Required) | Codeforces user handle.                                                                                                             |
| **from**              | 1-based index of the first submission to return.                                                                                    |
| **count**             | Number of returned submissions.                                                                                                     |
| **includeSources**    | Specifies whether source codes should be included in the output. This option is only available when requested for your own account. |

**Return value**: Returns a list of [Submission](/apiHelp/objects#Submission) objects, sorted in decreasing order of submission id.

**Example**: [https://codeforces.com/api/user.status?handle=Fefer\_Ivan&amp;from=1&amp;count=10](https://codeforces.com/api/user.status?handle=Fefer_Ivan&from=1&count=10)
