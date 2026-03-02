using System;
using System.Collections.Generic;
using System.Diagnostics;
using System.IO;
using System.Linq;
using System.Threading;

// ============================================================
//  PICKLEBALL COACH
//  A program to track player progress, log games, run drills,
//  and access coaching tips.
// ============================================================

// ─────────────────────────────────────────────────────────────
//  ENTRY POINT
// ─────────────────────────────────────────────────────────────
class Program
{
    static bool running = true;
    static List<Player> players = new List<Player>();
    static List<Tip> tips = new List<Tip>()
    {
        new Tip(2,  "Tip 1",    "https://www.youtube.com/watch?v=fsgJa0OgeRE"),
        new Tip(5,  "Tip 2",    "https://www.youtube.com/watch?v=Jgr4Yo9JrO4"),
        new Tip(7,  "Tip 3",    "https://www.youtube.com/watch?v=-raCQ4em4Lc"),
        new Tip(9,  "Tip 4",    "https://www.youtube.com/watch?v=ZkYLOfyAUr8"),
        new Tip(12, "Tip 5",    "https://www.youtube.com/watch?v=5bnLUkNb7PA"),
        new Tip(0,  "Free Tip", "https://www.youtube.com/watch?v=xEYsymCtIDY")
    };
    static List<Game> games = new List<Game>();

    static void Main(string[] args)
    {
        Console.Clear();
        Console.WriteLine("Welcome to the Pickleball Trainer\n");
        Console.WriteLine("In this program you will be able to track your progress on your pickleball journey.\n");
        Console.WriteLine("As you complete training sessions, level up your shots to improve your game.");
        Console.WriteLine("You will also be able to log your games to keep track of scores.");
        Console.Write("\nPress Enter to continue: ");
        Console.ReadLine();
        Console.Clear();

        while (running)
        {
            Console.WriteLine("\n");
            DisplayMenu();
        }
    }

    // ── Helpers ───────────────────────────────────────────────

    static void OpenLink(string link)
    {
        try
        {
            Process.Start(new ProcessStartInfo { FileName = link, UseShellExecute = true });
        }
        catch (Exception ex)
        {
            Console.WriteLine($"An error occurred: {ex.Message}");
        }
    }

    static string PlayerSelection()
    {
        int j = 1;
        foreach (Player guy in players)
        {
            Console.WriteLine($"{j}. {guy.getName()}");
            j++;
        }
        Console.Write("Select Player: ");
        int input = int.Parse(Console.ReadLine()) - 1;
        return players[input].getName();
    }

    static void ClearFile(string filename)
    {
        using (StreamWriter sw = new StreamWriter(filename, false))
        {
            sw.Write("");
        }
    }

    // ── Main Menu ─────────────────────────────────────────────

    static void DisplayMenu()
    {
        Console.WriteLine("Menu:");
        Console.WriteLine("1. Create Player");
        Console.WriteLine("2. Guided Practice");
        Console.WriteLine("3. Log Game");
        Console.WriteLine("4. View Games");
        Console.WriteLine("5. View Stats");
        Console.WriteLine("6. Tip Store");
        Console.WriteLine("7. Load");
        Console.WriteLine("8. Save and Quit");
        Console.WriteLine("9. Show List of Players");
        Console.Write("\nWhat would you like to do? ");
        string response = Console.ReadLine();

        switch (response)
        {
            // ── 1. Create Player ──────────────────────────────
            case "1":
                Console.Write("How many players would you like to add? ");
                int playersToAdd = int.Parse(Console.ReadLine());
                for (int i = 0; i < playersToAdd; i++)
                {
                    players.Add(new Player());
                    Console.WriteLine();
                }
                break;

            // ── 2. Guided Practice ────────────────────────────
            case "2":
                Console.WriteLine("1. Forehand");
                Console.WriteLine("2. Backhand");
                Console.WriteLine("3. Drop Shot");
                Console.Write("\nWhich shot would you like to practice? ");
                int shotChoice = int.Parse(Console.ReadLine());
                Console.Clear();

                int j = 1;
                foreach (Player p in players)
                {
                    Console.WriteLine($"{j}. {p.getName()}");
                    j++;
                }
                Console.Write("Which player is completing the practice? ");
                int playerIndex = int.Parse(Console.ReadLine()) - 1;
                Player student = players[playerIndex];

                if (shotChoice == 1)
                {
                    ForehandDrill drill = new ForehandDrill();
                    student.setExperience(drill.getPoints());
                    student.getShots()[shotChoice - 1].upDateShotLevel(drill.getPoints());
                }
                else if (shotChoice == 2)
                {
                    BackhandDrill drill = new BackhandDrill();
                    student.setExperience(drill.getPoints());
                    student.getShots()[shotChoice - 1].upDateShotLevel(drill.getPoints());
                }
                else if (shotChoice == 3)
                {
                    DropShotDrill drill = new DropShotDrill();
                    student.setExperience(drill.getPoints());
                    student.getShots()[shotChoice - 1].upDateShotLevel(drill.getPoints());
                }
                else
                {
                    Console.WriteLine("Invalid shot selection.");
                }
                break;

            // ── 3. Log Game ───────────────────────────────────
            case "3":
                Console.WriteLine("1. Singles");
                Console.WriteLine("2. Doubles");
                Console.Write("Which type of game do you want to log? ");
                int gameType = int.Parse(Console.ReadLine());

                if (gameType == 1)
                {
                    Console.WriteLine("Who is the first player?");
                    string p1 = PlayerSelection();
                    Console.WriteLine("Who is the second player?");
                    string p2 = PlayerSelection();
                    SinglesGame singles = new SinglesGame(p1, p2);
                    games.Add(singles);
                    Console.WriteLine(singles);

                    if (singles.getScoreTeam1() > singles.getScoreTeam2())
                    {
                        foreach (Player player in players)
                        {
                            if (player.getName() == p1)
                            {
                                player.setExperience(.25m);
                                player.SinglesWon();
                            }
                            // BUG FIX: was checking p1 twice; should penalise the loser (p2)
                            if (player.getName() == p2 && player.getExperience() >= .0125m)
                            {
                                player.setExperience(-.25m);
                            }
                        }
                    }
                    else if (singles.getScoreTeam1() < singles.getScoreTeam2())
                    {
                        foreach (Player player in players)
                        {
                            if (player.getName() == p2)
                            {
                                player.setExperience(.25m);
                                player.SinglesWon();
                            }
                            if (player.getName() == p1 && player.getExperience() >= .0125m)
                            {
                                player.setExperience(-.25m);
                            }
                        }
                    }
                }
                else if (gameType == 2)
                {
                    Console.WriteLine("Who is team one's first player?");
                    string p1 = PlayerSelection();
                    Console.WriteLine("Who is team one's second player?");
                    string p2 = PlayerSelection();
                    Console.WriteLine("Who is team two's first player?");
                    string p3 = PlayerSelection();
                    Console.WriteLine("Who is team two's second player?");
                    string p4 = PlayerSelection();
                    DoublesGame doubles = new DoublesGame(p1, p2, p3, p4);
                    games.Add(doubles);
                    Console.WriteLine(doubles);

                    if (doubles.getScoreTeam1() > doubles.getScoreTeam2())
                    {
                        foreach (Player player in players)
                        {
                            if (player.getName() == p1 || player.getName() == p2)
                            {
                                player.setExperience(.25m);
                                player.DoublesWon();
                            }
                            if ((player.getName() == p3 || player.getName() == p4) && player.getExperience() >= .0125m)
                            {
                                player.setExperience(-.25m);
                            }
                        }
                    }
                    else if (doubles.getScoreTeam1() < doubles.getScoreTeam2())
                    {
                        foreach (Player player in players)
                        {
                            if (player.getName() == p3 || player.getName() == p4)
                            {
                                player.setExperience(.25m);
                                player.DoublesWon();
                            }
                            if ((player.getName() == p1 || player.getName() == p2) && player.getExperience() >= .0125m)
                            {
                                player.setExperience(-.25m);
                            }
                        }
                    }
                }
                break;

            // ── 4. View Games ─────────────────────────────────
            case "4":
                int gameNum = 1;
                foreach (Game game in games)
                {
                    Console.WriteLine($"Game #{gameNum} {game}");
                    gameNum++;
                }
                break;

            // ── 5. View Stats ─────────────────────────────────
            case "5":
                foreach (Player player in players)
                {
                    Console.WriteLine($"{player.getName()}  Level: {player.getExperience()}");
                    foreach (Shot shot in player.getShots())
                    {
                        Console.WriteLine($"    {shot.getName()}: {shot.getShotLevel()}");
                    }
                    Console.WriteLine("    Games Won:");
                    Console.WriteLine($"       Singles: {player.getGamesWonSingles()}");
                    Console.WriteLine($"       Doubles: {player.getGamesWonDoubles()}");
                    Console.WriteLine();
                }
                break;

            // ── 6. Tip Store ──────────────────────────────────
            case "6":
                Console.Clear();
                if (players.Count == 0)
                {
                    Console.WriteLine("Create a player first.");
                    break;
                }
                j = 1;
                foreach (Player p in players)
                {
                    Console.WriteLine($"{j}. {p.getName()}");
                    j++;
                }
                Console.Write("Which player? ");
                int tipPlayerIndex = int.Parse(Console.ReadLine()) - 1;
                student = players[tipPlayerIndex];
                decimal level = student.getExperience();

                int h = 1;
                foreach (Tip tip in tips)
                {
                    Console.WriteLine();
                    if (level >= tip.getRequiredLevel())
                        Console.WriteLine($"{h}. {tip.getName()}");
                    else
                        Console.WriteLine($"{h}. Get to level {tip.getRequiredLevel()} to unlock this tip");
                    h++;
                }
                Console.Write("Which tip would you like to view? ");
                int selection = int.Parse(Console.ReadLine()) - 1;
                if (level >= tips[selection].getRequiredLevel())
                    OpenLink(tips[selection].getLink());
                else
                    Console.WriteLine("Need more experience to unlock this tip.");
                break;

            // ── 7. Load ───────────────────────────────────────
            case "7":
                string loadFile = "TennisProgram.txt";
                string[] lines = File.ReadAllLines(loadFile);
                foreach (string line in lines)
                {
                    string[] parts = line.Split("||");
                    string type = parts[0];
                    switch (type)
                    {
                        case "Player":
                            string name       = parts[1];
                            string age        = parts[2];
                            decimal exp       = decimal.Parse(parts[3]);
                            decimal forehand  = decimal.Parse(parts[4]);
                            decimal backhand  = decimal.Parse(parts[5]);
                            decimal dropshot  = decimal.Parse(parts[6]);
                            int singlesWon    = int.Parse(parts[7]);
                            int doublesWon    = int.Parse(parts[8]);
                            players.Add(new Player(name, age, exp, forehand, backhand, dropshot, singlesWon, doublesWon));
                            break;
                        case "SinglesGame":
                            string sp1       = parts[1];
                            int sp1score     = int.Parse(parts[2]);
                            string sp2       = parts[3];
                            int sp2score     = int.Parse(parts[4]);
                            games.Add(new SinglesGame(sp1, sp1score, sp2, sp2score));
                            break;
                        case "DoublesGame":
                            string dp1       = parts[1];
                            string dp2       = parts[2];
                            int dp1score     = int.Parse(parts[3]);
                            string dp3       = parts[4];
                            string dp4       = parts[5];
                            int dp2score     = int.Parse(parts[6]);
                            games.Add(new DoublesGame(dp1, dp2, dp1score, dp3, dp4, dp2score));
                            break;
                        default:
                            Console.WriteLine("Unknown record type — skipping.");
                            break;
                    }
                }
                break;

            // ── 8. Save and Quit ──────────────────────────────
            case "8":
                string saveFile = "TennisProgram.txt";
                Console.WriteLine("Would you like to overwrite or add to the file?");
                Console.WriteLine("(1) Overwrite  (2) Add");
                Console.Write("Choice: ");
                string saveChoice = Console.ReadLine();
                if (saveChoice == "1")
                    ClearFile(saveFile);

                foreach (Player player in players)
                    player.savePlayer(saveFile);
                foreach (Game game in games)
                    game.saveGame(saveFile);

                running = false;
                break;

            // ── 9. Show Player List ───────────────────────────
            case "9":
                foreach (Player person in players)
                    Console.WriteLine(person.displayInfo());
                break;

            default:
                Console.WriteLine("Invalid option. Please enter a number 1–9.");
                break;
        }
    }
}

// ─────────────────────────────────────────────────────────────
//  SHOT CLASSES
// ─────────────────────────────────────────────────────────────
class Shot
{
    private decimal _shotLevel;
    private string _shotName;

    public Shot(string name)
    {
        _shotName = name;
        _shotLevel = 0;
    }
    public Shot(string name, decimal level)
    {
        _shotName = name;
        _shotLevel = level;
    }
    public decimal getShotLevel() => _shotLevel;
    public string getName() => _shotName;
    public void upDateShotLevel(decimal num) => _shotLevel += num * 0.025m;
}

class ForehandShot : Shot
{
    public ForehandShot() : base("Forehand") { }
    public ForehandShot(decimal num) : base("Forehand", num) { }
}

class BackhandShot : Shot
{
    public BackhandShot() : base("Backhand") { }
    public BackhandShot(decimal num) : base("Backhand", num) { }
}

class DropShot : Shot
{
    public DropShot() : base("DropShot") { }
    public DropShot(decimal num) : base("DropShot", num) { }
}

// ─────────────────────────────────────────────────────────────
//  PLAYER
// ─────────────────────────────────────────────────────────────
class Player
{
    private string _name;
    private string _age;
    private decimal _experience;
    private ForehandShot _forehand;
    private BackhandShot _backhand;
    private DropShot _dropshot;
    private List<Shot> _shots;   // BUG FIX: was static — caused all players to share the same shot list
    private int _singlesWon;
    private int _doublesWon;

    public Player()
    {
        Console.Write("Name: ");
        _name = Console.ReadLine();
        Console.Write("Age: ");
        _age = Console.ReadLine();
        _experience = 0;
        _singlesWon = 0;
        _doublesWon = 0;
        InitShots(0, 0, 0);
    }

    public Player(string name, string age, decimal experience,
                  decimal fore, decimal back, decimal drop,
                  int singlesWon, int doublesWon)
    {
        _name = name;
        _age = age;
        _experience = experience;
        _singlesWon = singlesWon;
        _doublesWon = doublesWon;
        InitShots(fore, back, drop);
    }

    private void InitShots(decimal fore, decimal back, decimal drop)
    {
        _forehand = fore == 0 ? new ForehandShot() : new ForehandShot(fore);
        _backhand = back == 0 ? new BackhandShot() : new BackhandShot(back);
        _dropshot = drop == 0 ? new DropShot()     : new DropShot(drop);
        _shots = new List<Shot> { _forehand, _backhand, _dropshot };
    }

    public void SinglesWon()  => _singlesWon++;
    public void DoublesWon()  => _doublesWon++;   // BUG FIX: was incrementing _singlesWon instead of _doublesWon

    public int getGamesWonSingles() => _singlesWon;
    public int getGamesWonDoubles() => _doublesWon;

    public string getName()        => _name;
    public string getAge()         => _age;
    public decimal getExperience() => _experience;
    public List<Shot> getShots()   => _shots;

    public void setExperience(decimal num) => _experience += num * 0.050m;

    public string displayInfo() =>
        $"{_name}\n   Age: {_age}\n   Experience: {_experience}\n";

    public void savePlayer(string filename)
    {
        using (StreamWriter sw = new StreamWriter(filename, true))
        {
            sw.WriteLine($"Player||{_name}||{_age}||{_experience}" +
                         $"||{_forehand.getShotLevel()}||{_backhand.getShotLevel()}" +
                         $"||{_dropshot.getShotLevel()}||{_singlesWon}||{_doublesWon}");
        }
    }
}

// ─────────────────────────────────────────────────────────────
//  GAME CLASSES
// ─────────────────────────────────────────────────────────────
class Game
{
    protected int _team1score { get; set; }
    protected int _team2score { get; set; }
    protected string player1 { get; private set; }
    protected string player2 { get; private set; }

    public Game(string one, string two)
    {
        player1 = one;
        player2 = two;
        Console.Write("What was the score of team one? ");
        _team1score = int.Parse(Console.ReadLine());
        Console.Write("What was the score of team two? ");
        _team2score = int.Parse(Console.ReadLine());
    }

    public Game(string one, int score1, string two, int score2)
    {
        player1 = one;
        player2 = two;
        _team1score = score1;
        _team2score = score2;
    }

    public int getScoreTeam1() => _team1score;
    public int getScoreTeam2() => _team2score;

    public override string ToString() =>
        $"{player1}({_team1score}) : {player2}({_team2score})";

    public virtual void saveGame(string filename)
    {
        using (StreamWriter sw = new StreamWriter(filename, true))
        {
            sw.WriteLine($"SinglesGame||{player1}||{_team1score}||{player2}||{_team2score}");
        }
    }
}

class SinglesGame : Game
{
    public SinglesGame(string one, string two) : base(one, two) { }
    public SinglesGame(string p1, int s1, string p2, int s2) : base(p1, s1, p2, s2) { }
}

class DoublesGame : Game
{
    private string _player3;
    private string _player4;

    public DoublesGame(string one, string two, string three, string four) : base(one, two)
    {
        _player3 = three;
        _player4 = four;
    }

    public DoublesGame(string p1, string p2, int score1, string p3, string p4, int score2)
        : base(p1, score1, p2, score2)
    {
        _player3 = p3;
        _player4 = p4;
    }

    public override string ToString() =>
        $"{player1} and {player2}({_team1score}) : {_player3} and {_player4}({_team2score})";

    public override void saveGame(string filename)
    {
        using (StreamWriter sw = new StreamWriter(filename, true))
        {
            sw.WriteLine($"DoublesGame||{player1}||{player2}||{_team1score}||{_player3}||{_player4}||{_team2score}");
        }
    }
}

// ─────────────────────────────────────────────────────────────
//  DRILL BASE CLASS
// ─────────────────────────────────────────────────────────────
class Drill
{
    private string _name;
    private string _description;
    private decimal _points;
    private string _setup;
    private string _objective;
    private string _execution;

    public Drill(string name, string description, decimal points,
                 string setup, string objective, string execution)
    {
        _name = name;
        _description = description;
        _points = points;
        _setup = setup;
        _objective = objective;
        _execution = execution;

        Console.WriteLine($"{_name}:\n{_description}");
        Console.WriteLine($"You will receive {_points} experience by completing this practice.");
        Console.Write("Press Enter to begin. ");
        Console.ReadLine();
        RunDrill();
    }

    public decimal getPoints() => _points;

    private void RunDrill()
    {
        Console.Clear();
        LoadAnimation();
        Console.WriteLine(_name);
        Console.WriteLine(_objective);
        EnterContinue();
        Console.WriteLine(_setup);
        Console.WriteLine(_execution);
        LoadAnimation();
        Console.WriteLine($"\nYou have completed the {_name}. You received {_points} experience points!");
    }

    private void LoadAnimation()
    {
        for (int i = 0; i < 5; i++)
        {
            foreach (char c in new[] { '-', '\\', '|', '/' })
            {
                Console.Write(c);
                Thread.Sleep(200);
                Console.Write("\b \b");
            }
        }
    }

    private void EnterContinue()
    {
        Console.Write("Press Enter to continue. ");
        Console.ReadLine();
    }
}

// ─────────────────────────────────────────────────────────────
//  DRILL SUBCLASSES
// ─────────────────────────────────────────────────────────────
class ForehandDrill : Drill
{
    public ForehandDrill() : base(
        "Forehand Practice",
        "Forehand shots are fundamental in pickleball, allowing players to generate power and control. Here's a drill to help you improve your forehand technique.",
        20,
        "Setup: Find a practice partner and a pickleball court. Position yourselves on opposite sides of the net, with one player serving and the other receiving.",
        "Objective: The goal of this drill is to practice executing effective forehand shots, focusing on power and consistency.",
        "Execution:\n" +
        "- Start by having the serving player initiate the rally with a serve to the receiving player's forehand side.\n" +
        "- After the receive, the receiving player should respond with a controlled forehand shot. Focus on proper footwork and racquet preparation.\n" +
        "- Aim to hit the ball cleanly with your forehand, generating power and directing it to different areas of the court with accuracy.\n" +
        "- Pay attention to your body positioning and weight transfer, ensuring balance and stability throughout the shot.\n" +
        "- The serving player should then attempt to return the forehand shot with a soft volley or an aggressive shot, depending on the situation.\n" +
        "- Continue rallying back and forth, alternating between serving and receiving, with both players focusing on quality forehand shots."
    )
    { }
}

class BackhandDrill : Drill
{
    public BackhandDrill() : base(
        "Backhand Practice",
        "Backhand shots are essential in pickleball, requiring precision and control to effectively return balls from your opponent. Here's a drill to help you improve your backhand technique.",
        25,
        "Setup: Find a practice partner and a pickleball court. Position yourselves on opposite sides of the net, with one player serving and the other receiving.",
        "Objective: The goal of this drill is to practice executing effective backhand shots, focusing on consistency and placement.",
        "Execution:\n" +
        "- Start by having the serving player initiate the rally with a serve to the receiving player's backhand side.\n" +
        "- After the receive, the receiving player should respond with a controlled backhand shot. Focus on proper footwork and racquet preparation.\n" +
        "- Aim to hit the ball cleanly with your backhand, directing it to different areas of the court with accuracy.\n" +
        "- Pay attention to your body positioning and weight transfer, ensuring balance and stability throughout the shot.\n" +
        "- The serving player should then attempt to return the backhand shot with a soft volley or an aggressive shot.\n" +
        "- Continue rallying back and forth, alternating between serving and receiving, with both players focusing on quality backhand shots."
    )
    { }
}

class DropShotDrill : Drill
{
    public DropShotDrill() : base(
        "Drop Shot Practice",
        "The drop shot is a finesse shot in pickleball that requires delicate touch and precise placement to softly land the ball just over the net, ideally in the non-volley zone (the kitchen). Here's a drill to help you improve your drop shot technique.",
        30,
        "Setup: Find a practice partner and a pickleball court. Position yourselves on opposite sides of the net, with one player serving and the other receiving.",
        "Objective: The goal of this drill is to practice executing effective drop shots, focusing on placement and control.",
        "Execution:\n" +
        "- Start by having the serving player initiate the rally with a serve to the receiving player's forehand or backhand side.\n" +
        "- After the receive, the receiving player should respond with a controlled drop shot, aiming to softly place the ball just over the net in the opponent's non-volley zone.\n" +
        "- Focus on a gentle, controlled swing motion. Keep your wrist firm but relaxed for precise placement.\n" +
        "- Aim to land the drop shot close to the net, making it difficult for your opponent to return effectively.\n" +
        "- The serving player should then attempt to return the drop shot with a soft volley or their own drop shot.\n" +
        "- Continue rallying back and forth, alternating between serving and receiving, with both players focusing on quality drop shots."
    )
    { }
}

// ─────────────────────────────────────────────────────────────
//  TIP
// ─────────────────────────────────────────────────────────────
class Tip
{
    private int _requiredLevel;
    private string _tipName;
    private string _tipLink;

    public Tip(int level, string name, string link)
    {
        _requiredLevel = level;
        _tipName = name;
        _tipLink = link;
    }

    public string getName()        => _tipName;
    public int getRequiredLevel()  => _requiredLevel;
    public string getLink()        => _tipLink;
}
