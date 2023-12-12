package monitoring;

import org.apache.commons.cli.*;

import java.io.FileWriter;
import java.io.IOException;

public class Main {
    public static void main(String[] args) {
        Option routesFileOpt = Option.builder().longOpt("routes").argName("ROUTES").required().hasArg()
                .desc("routes file").build();

        Option goalOpt = Option.builder().longOpt("goal").argName("GOAL").required().hasArg()
                .desc("goal (cover or 1id)").build();

        Option statsOutOpt = Option.builder().longOpt("print-csv").hasArg(false)
                .desc("print statistic").build();

        Option solOutOpt = Option.builder().longOpt("print-solution").hasArg(false)
                .desc("print solution").build();

        Option solFileOpt = Option.builder().longOpt("write-solution").hasArg()
                .desc("file to write the solution").build();

        Options options = new Options();
        options.addOption(routesFileOpt);
        options.addOption(goalOpt);
        options.addOption(statsOutOpt);
        options.addOption(solOutOpt);
        options.addOption(solFileOpt);

        CommandLineParser parser = new DefaultParser();
        CommandLine cmd = null;
        try {
            cmd = parser.parse(options, args);
        } catch (ParseException exp) {
            System.err.println(exp.getMessage());
            new HelpFormatter().printHelp("solve path selection problem", options);
            System.exit(1);
        }

        String problemType = cmd.getOptionValue("problem");
        String routeFilename = cmd.getOptionValue("routes");
        String goal = cmd.getOptionValue("goal");
        boolean oneId = goal.equals("1id");

        // Initialize the problem
        Problem problem;
        problem = new MonitorSelection(routeFilename, oneId);

        // Solve the problem
        long startTime = System.currentTimeMillis();
        problem.solve();
        long endTime = System.currentTimeMillis();
        double solvingTime = (endTime - startTime) / 1000.0;
        boolean isCovered = problem.verifyCover();
        boolean isOneId = problem.verifyOneId();

        // Output the statistics
        if (cmd.hasOption("print-csv")) {
            String output = "";
            output += routeFilename + ";greedy;" + goal + ";" + ((MonitorSelection) problem).getMonitors().size()
                        + ";" + isCovered + ";" + isOneId + ";" + solvingTime;
            output += ";" + ((MonitorSelection) problem).nbrCover +
                        ";" + ((MonitorSelection) problem).nbrOneId +
                        ";" + ((MonitorSelection) problem).nbrReduction;
            System.out.println(output);
        }
        else {
            System.out.println("Number of monitors : " + ((MonitorSelection) problem).getMonitors().size());
            System.out.println("Solving Time (s) : " + solvingTime);
            System.out.println("Covered : " +isCovered);
            System.out.println("1-identifiable : " + isOneId);
        }

        // Print the solution
        if (cmd.hasOption("print-solution")) {
            System.out.println(solvingTime);
            System.out.print(problem.solutionString());
        }

        // Write the solution in the given file
        if (cmd.hasOption("write-solution")) {
            try {
                FileWriter solutionOutput = new FileWriter(args[2]);
                String solution = problem.solutionString();
                solutionOutput.write(solution);
                solutionOutput.close();
            }catch (IOException e) {
                System.out.println(e);
            }
        }

    }
}
