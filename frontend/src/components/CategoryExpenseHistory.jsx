function CategoryExpenseHistory({

  data = {}

}) {

  return (

    <div className="card">

      <h2>
        Category Expense History
      </h2>

      {

        Object.entries(data).map(
          ([category, expenses]) => (

            <div
              key={category}
              style={{
                marginBottom: "25px"
              }}
            >

              <h3>
                {category.toUpperCase()}
              </h3>

              <table
                width="100%"
              >

                <thead>

                  <tr>

                    <th>
                      Title
                    </th>

                    <th>
                      Amount
                    </th>

                  </tr>

                </thead>

                <tbody>

                  {

                    expenses.map(
                      expense => (

                        <tr
                          key={expense.id}
                        >

                          <td>
                            {
                              expense.title
                            }
                          </td>

                          <td>
                            ₹{
                              expense.amount
                            }
                          </td>

                        </tr>

                      )
                    )

                  }

                </tbody>

              </table>

            </div>

          )
        )

      }

    </div>

  )

}

export default CategoryExpenseHistory