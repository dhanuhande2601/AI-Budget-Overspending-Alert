function LatestExpenses({

  expenses = {}

}) {

  return (

    <div className="card">

      <h2>

        Latest 10 Expenses By Category

      </h2>

      {

        Object.keys(
          expenses
        ).length === 0

        ?

        <p>

          No expenses found

        </p>

        :

        Object.entries(
          expenses
        ).map(

          ([category, items]) => (

            <div
              key={category}
              style={{
                marginBottom: '20px'
              }}
            >

              <h3
                style={{
                  textTransform:
                    'capitalize'
                }}
              >

                {category}

              </h3>

              <table>

                <thead>

                  <tr>

                    <th>

                      Title

                    </th>

                    <th>

                      Amount

                    </th>

                    <th>

                      Date

                    </th>

                  </tr>

                </thead>

                <tbody>

                  {

                    items.map(

                      (
                        item,
                        index
                      ) => (

                        <tr
                          key={index}
                        >

                          <td>

                            {item.title}

                          </td>

                          <td>

                            ₹{item.amount}

                          </td>

                          <td>

                            {
                              item.date ||
                              '-'
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

export default LatestExpenses