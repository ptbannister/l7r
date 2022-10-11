L7R Combat Simulator
--------------------

# Requirements
* Python 3.8 or better
* pyyaml module (run `pip install pyyaml` to get it)


# Installing

You can run the L7R combat simulator by cloning the l7r git repository,
checking out the "new-simulator" branch, and running it on the command line.


# Running

Open a command prompt, change directories to the l7r directory from your
clone of the git repo, and run:
`python -m simulation -h`

This will explain your command line arguments. The simplest way to run is:
`python -m simulation -i path-to-characters -t number-of-trials`
where "path-to-characters" is the name of a directory where you've saved
character and group files, and "number-of-trials" is the number of trials
you want to run for a simulation.

If you include the argument `--log-level info` then you will get an event
log in a file called "simulation.log" in your working directory. You may
do `--log-level debug` instead for more verbose output, but the extra
information is unlikely to be interesting unless you're investigating bugs.


# Input: Character and Group Files

You can create characters and assign them to groups by writing YAML format
files.

Character files may have any name. The groups file must be called "groups.yaml".
An input directory may have any number of character files, but it must have one
and only one groups file.


## Groups File (groups.yaml)

The groups file must be named "groups.yaml". It defines two groups, indicates
which group is the control group and which group is the test group, and defines
the characters in each group.

A groups file looks like this:

```
east:
  control: true
  characters:
  - Akodo
  - Doji
west:
  test: true
  characters:
  - Bayushi
  - Hida
```

The `characters` section of a group should list the names of the characters in
the group. The names must be the same names that appear in the character files.


## Character Files

Character files may use any filename and any file extension.

A character file must have the sections:
* name
* rings
* skills

It may have either a school, or a profession, or neither.

It may also have the optional sections:
* xp
* advantages
* disadvantages
* strategies

An example character file looks like this:
```
name: Taro
xp: 9001
rings:
  air: 2
  earth: 3
  fire: 4
  water: 3
  void: 3
skills:
  attack: 4
  parry: 5
advantages:
- strength of the earth
- great destiny
disadvantages:
- contrary
- long temper
- meddler
- proud
- short temper
- transparent
- vain
strategies:
  action: AlwaysAttackActionStrategy
  parry: NeverParryStrategy
```

### Character Name

The character name defines the character's name. It must match the name
in the groups file.

If the name field is omitted, the character will be assigned a random UUID
as its name. Since you have to name the character in the groups file, a
random name isn't going to work out, so make sure to provide a name!


### Character XP

The xp field defines the number of Experience Points used to build the character.

If omitted, the character will be given 100 XP.

The XP field is enforced, so if you don't want to calculate how many XP it takes
to build your character, it is recommended to specify a very large number such as
9001.


### Character School, Profession, or Neither

You may put a "school" or "profession", or neither.


#### Characters with Samurai Schools

Characters with a samurai school receive many benefits:
* School ring raised to 3 for free
* Attack and Parry start at 1 for free
* School knacks start at 1 for free

The following schools are available:
* Akodo Bushi School
* Bayushi Bushi School
* Shiba Bushi School


#### Characters with Peasant Professions

Characters with a profession have to buy their first ranks of Attack and Parry,
and do not receive the free ring raise to 3. However, they gain profession
abilities.

Professions are not yet supported.


#### Characters without School or Profession

You may also build a "generic" character that does not have a profession or a school.

In this case, you will have to pay for your first ranks of Attack and Parry, and you
will not gain profession abilities.


### Character Rings

Rings are required.

The Rings are:
* air
* earth
* fire
* water
* void

Allowed values are between 2 and 5.
A character with a school may set their school ring to 6.


### Character Skills

Skills are required.

The skills supported in the simulator are:
* attack
* double attack
* feint (although strategies to use it are lacking)
* parry

We plan to add support in the near future for:
* counterattack
* iaijutsu
* lunge

You may also put other valid L7R skills, but they are not
used in the simulator at this time.


### Character Advantages

Characters may buy advantages at character creation time.
All of the advantages from the core rules are supported,
but the only advantages that have any mechanical effect at
this time are:
* Great Destiny
* Strength of the Earth


### Character Disadvantages

Characters may take disadvantages at character creation time.
All disadvantages from the core rules are supported,
but the only advantages that have any mechanical effect at
this time are:
* Permanent Wound


### Character Strategies

Strategies are used to determine character behavior. You may override
strategies to customize a character's behavior.

Strategies are the most important part of the simulator, and also the
most difficult to write.

You should be careful about overriding the strategies of a character
with a school or profession! Certain schools have a custom strategies
that take into account their special abilities. Overriding their
strategies may result in nerfing the character's school or profession
abilities.


#### Action Strategies

A character's action strategy determines whether to act when an action
is available.

Specify an action strategy like this:
```
strategies:
  action: NameOfStrategy
```

Available action strategies are:
* `AlwaysAttackActionStrategy`: always attack as soon as an action is available
* `HoldOneActionStrategy`: do not attack unless you have two available actions,
until Phase 10

The default action strategy is `HoldOneActionStrategy`.


#### Attack Strategies

Attack strategies determine how a character attacks.

Specify an attack strategy like this:
```
strategies:
  attack: NameOfStrategy
```

Available attack strategies are:
* `PlainAttackStrategy`: find the easiest character to hit, and use the attack skill to attack them.
Spend Void Points if it is likely the attack roll would result in keeping additional damage dice.
* `StingyPlainAttackStrategy`: like `PlainAttackStrategy`, but never spend VP.
* `UniversalAttackStrategy`: find the easiest character to hit. Try double attack first, then consider
a feint if out of VP, then fall back to a plain attack. Spend VP if probable to get extra kept damage dice.

The default attack strategy is `UniversalAttackStrategy`.


#### Parry Strategies

Parry strategies determine whether and how a character parries.

Specify a parry strategy like this:
```
strategies:
  parry: NameOfStrategy
```

Available parry strategies are:
* `AlwaysParryStrategy`: always parry an attack after it is rolled if it's a hit.
* `NeverParryStrategy`: never parry an attack.
* `ReluctantParryStrategy`: parry an attack if it's expected to deal more than 2 SW.
Try to shirk parrying for a friend unless you are the only person who can do it.

The default parry strategy is `ReluctantParryStrategy`.


#### Light Wounds Strategies

Light wounds strategies determine whether to keep light wound after a successful wound check.

Specify a light wounds strategy like this:
```
strategies:
  light_wounds: NameOfStrategy
```

Available light wounds strategies are:
* `AlwaysKeepLightWoundsStrategy`: always keep light wounds after a successful wound check.
* `KeepLightWoundsStrategy`: keep light wounds if the average damage rolls made by the enemy
group would make the next wound check dangerous (chance of taking more than 2 SW on the next
wound check is greater than 50%).
* `NeverKeepLightWoundsStrategy`: always take a Serious Wound after a successful wound check.

The default light wounds strategy is `KeepLightWoundsStrategy`.


### Wound Check Strategies

Wound check strategies determine how many Void Points to spend on a wound check.

Specify a wound check strategy like this:
```
strategies:
  wound_check: NameOfStrategy
```

Available wound check strategies are:
* `StingyWoundCheckStrategy`: never spend Void Points on wound checks.
* `WoundCheckStrategy`: if this character's average wound check roll would result in taking
more than 1 Serious Wound, spend as many VP as possible until the expected number of
Serious Wounds is reduced to 1.

The default wound check strategy is `WoundCheckStrategy`.


# Output

The simulator outputs a CSV file in the output directory (set by the `-o` flag) that
gives statistics captured from each trial run. The data in this file is used to
generate a summary report that is printed to the command line after a run.

The report gives the test group's win rate and some stats about the test and control
group. It gives the same stats again "given test group victory" and "given control
group victory", which means that the second and third reports are statistics for only
the trials where the test group won or the control group won. This is intended to
help determine what kinds of variables reinforce or undercut a certain strategy. For
example, certain characters, schools, or strategies may be seriously undercut by
a certain kind of unlucky roll.

