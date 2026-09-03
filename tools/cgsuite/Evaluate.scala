// Headless CGSuite driver: evaluate one expression per input line, print
// "expression <TAB> result". Errors are reported inline as "!! message" so a
// failing query never aborts the batch.
//
// Blank lines and lines starting with '#' are ignored, so a query file can be
// commented and grouped.
import org.cgsuite.lang.System
import scala.collection.mutable
import scala.io.Source

object Evaluate {
  def main(args: Array[String]): Unit = {
    if (args.isEmpty) {
      Console.err.println("usage: Evaluate <query-file>")
      sys.exit(2)
    }
    val lines = Source.fromFile(args(0), "UTF-8").getLines().toVector
      .map(_.trim).filter(l => l.nonEmpty && !l.startsWith("#"))
    // Warm-up. The `game` package resolves only once class loading has been
    // triggered, so a batch whose *first* query is `game.heap.X` fails with
    // "That variable is not defined: `game`" unless something precedes it.
    // This cost an hour to diagnose; do not remove it.
    try System.evaluateOrException("*[0]", mutable.AnyRefMap[Symbol, Any]())
    catch { case _: Throwable => () }
    for (line <- lines) {
      val varMap = mutable.AnyRefMap[Symbol, Any]()
      val result =
        try System.evaluateOrException(line, varMap).map(_.toString).mkString(" ")
        catch { case e: Throwable => "!! " + e.getClass.getSimpleName + ": " + e.getMessage }
      println(line + "\t" + result)
      // Flush per line so a long batch can be watched, and so a batch killed
      // by a timeout still yields everything computed up to that point.
      Console.flush()
    }
  }
}
