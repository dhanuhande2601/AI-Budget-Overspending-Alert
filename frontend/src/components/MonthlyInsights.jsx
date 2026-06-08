function MonthlyInsights({

  data

}) {

  if (!data)
    return null

  return (

    <div className="card">

      <h2>
        Monthly Insights
      </h2>

      <p>

        Highest Category:
        {data.highest_category}

        (₹{data.highest_amount})

      </p>

      <p>

        Lowest Category:
        {data.lowest_category}

        (₹{data.lowest_amount})

      </p>

      <p>

        Transactions:
        {data.total_transactions}

      </p>

      <p>

        Average Expense:
        ₹{data.average_expense}

      </p>

      <p>

        Total Spending:
        ₹{data.total_spending}

      </p>

    </div>

  )

}

export default MonthlyInsights