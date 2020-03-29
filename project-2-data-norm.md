# Final Project Normalization
## Prep work
1. Create `tournament_id` based on `(level, year, name)` 
2. Create `ballot_id` as an auto-incrementing primary key

## Functional Dependencies
- ballot_id is a super key
- PD -> BallotResult
- (level, year, name) -> tournament_id
- tournament_id -> {name, division, start_date, end_date, host, location, tab_note_0, tab_note_1, amta_rep_0, amta_rep_1, amta_rep_2, bid_start_date, bid_end_date, bid_location, level}
- (tournament_id, TeamNum) -> {TotalWins, TotalTies, TotalLosses, TotalBallots, TeamName, EarnedBid, EarnedHonorableMention, WonSPAMTA, SPAMTAHonorableMention, SPAMTARanks, TotalCS, TotalOCS, TotalPD, Rank}
- (TotalWins, TotalTies) -> TotalBallots
- (TeamNum, year) -> TeamName
- (tournament_id, Rank) -> {EarnedBid, EarnedHonorableMention}
- (tournament_id, SPAMTARanks) -> {WonSPAMTA, SPAMTAHonorableMention}
- (tournament_id, TeamNum, RoundNum) -> {OppNum, OppName, Side}

## 0NF to 1NF
1. Convert tab_info rows into more specific pieces of info – first round coin flip, 6th place after R3, 7th_place_after_r3. Relabel these as more specific columns
2. Separate out students into new table `Student`
3. Separate AMTA reps into new table `AMTARep`

Here are the tables this yields:

> `Student`: <u>tournament_id, TeamNum, StudentNum</u>, Student, Role, Ranks, Side

> `AMTARep`: <u>tournament_id, num</u>, amta_rep

> `Remaining`: <u>ballot_id</u>, tournament_id, TeamNum, RoundNum, OppNum, Side, PD, BallotResult, TotalWins, TotalTies, TotalLosses, TotalBallots, TeamName, OppName, EarnedBid, EarnedHonorableMention, WonSPAMTA, SPAMTAHonorableMention, SPAMTARanks, name, division, start_date, end_date, host, location, first_coint_flip, second_coin_flip, bid_start_date, bid_end_date, bid_location, third_coin_flip, 7th_place_after_r3, TotalCS, TotalOCS, TotalPD, Rank, level

## 1NF to 2NF
There is only one key attribute. Therefore, necessarily, each attribute depends on the entire key.

## 2NF to 3NF
The functional dependencies above describe the attributes that are dependent on tournament_id. Breaking all of those out into a separate table, we get:

> ### Table 1: 
> `Tournament`: <u>tournament_id</u>, name, division, start_date, end_date, host, location, first_coint_flip, second_coin_flip, bid_start_date, bid_end_date, bid_location, third_coin_flip, level, 7th_place_after_r3
>> Note: In `Tournament`, there is a dependency between (year, level, (name|location|host)) and every other attribute. But, since that makes those super keys for the relationship, it's still in 3NF and BCNF.

Next, we have the dependency (tournament_id, Rank) -> {EarnedBid, EarnedHonorableMention}. This can be extracted to a separate table:

> `BidRecords`: <u>tournament_id, Rank</u>, EarnedBid, EarnedHonorableMention

However, this isn't the most efficient way to store that information. Specifically: there is some number of teams _n_ that earned a bid. All teams with a rank ≤ _n_ got a bid. Therefore, the more efficient way to store this information is to store the number of teams that got a bid:

> ### Table 2:
> `NumberOfBids`: <u>tournament_id</u>, NumberOfBids

Then, to see if a team got a bid at a tournament, you can simply check if that team's rank ≤ NumberOfBids for that tournament.

Next, there are two separate ways we could try to get TeamName from TeamNum – either with the key (TeamNum, tournament_id), or (TeamNum, year). Since tournament_id -> year, the latter key is more general. This gives us our third table:

> ### Table 3:
> `TeamName`: <u>year, TeamNum</u>, TeamName

Of the remaining columns, we have a large number of columns that depend on (tournament_id, team_num). But within these, there's another non-key dependency – TotalBallots depends on TotalWins and TotalTies (specifically – TotalBallots = TotalWins + (TotalTies/2)). We could create a separate table for these, but since the equation for finding it is so simple, it would be more efficient to do that calculation in a view, so we can just remove TotalBallots. This gives us another table:

> ### Table 4: 
> `Team`: <u>tournament_id, TeamNum</u>, TotalWins, TotalTies, TotalLosses, WonSPAMTA, SPAMTAHonorableMention, SPAMTARanks, TotalCS, TotalOCS, TotalPD, Rank

Here are the remaining columns: tournament_id, ballot_id, RoundNum, TeamNum, OppNum, OppName, Side, PD, BallotResult

At this point, we run into a weird issue: by separating out the team information, we fell back into 0NF. Each team has its own "copy" of each ballot/round information, but because it also had team-specific information, the rows weren't duplicated. Now, with that information, there are duplicate values. Specifically: for every row, there is an identical row with (TeamNum, TeamName) and (OppNum, OppName) switched.

To fix this, we need to exclude rows where `Side` = ∆. By doing this, we know that the TeamNum represents the π, and the OppNum represents the ∆. We can rename the columns to represent that – changing TeamNum to PlNum, and changing OppNum to DefNum. We should also exclude OppName/DefName, since the information of which Team # represents which team has already been extracted into `Team`.

Now, we can look at the information that can be extracted from only tournament_id, PlNum, and RoundNum: DefNum, Side. We can extract those into a new table:

> ### Table 5
> `Matchup`: <u>tournament_id, RoundNum, PlNum</u>, DefNum, Side

The only other attribute with a non-key dependency is `BallotResult`. Like with `TotalBallots`, we could extract this to its own table. But like with `TotalBallots`, the calculation is simple enough that we're better off removing it and using a view to re-do the calculation.

> ### Table 6:
> `Ballot`: <u>ballot_id</u>, tournament_id, RoundNum, PlNum, PD, BallotResult

### A Side Note (not for the final report)
Normalizing made it not easy to ask two vital questions: who did Team A play in Round x, and which side were they on? We haven't lost the data – for round x, there will be an entry in `Matchup` with Team A as either the plaintiff or the defense. At some point, we're going to need to make a view that has duplicate data by joining `Matchup` with itself – one from the "perspective" of the plaintiff, one from the "defense".
