# Smart Financial Reporting Tool (SFRT) - Financial Formulas & Accounting Specifications

This document outlines the mathematical formulas, accounting classifications, and data-quality rules implemented in SFRT.

## 1. Accounting Classifications

The system recognizes 9 discrete transaction classifications:

| Classification | Financial Treatment | Example |
| :--- | :--- | :--- |
| **Revenue** | Core operational business sales/services | Client invoices, store sales |
| **Other Income** | Secondary non-operating earnings | Interest, dividends, grants |
| **Operating Expense** | Ongoing overhead required to run operations | Rent, salaries, utilities, software |
| **Cost of Goods Sold (COGS)** | Direct costs attributable to product/service delivery | Inventory, raw materials, manufacturing costs |
| **Asset Purchase** | Capital expenditure (CapEx) | Equipment, vehicles, servers |
| **Liability Payment** | Debt principal service | Loan repayments |
| **Owner Contribution** | Equity injections by owner/shareholders | Founder seed funding |
| **Owner Withdrawal** | Drawings or distributions to owners | Personal drawings, dividends |
| **Transfer** | Internal balance movement between user accounts | Savings to checking transfer |

---

## 2. Mathematical Formulas

All arithmetic is executed using **Python Decimal** with 2-decimal-place rounding (`ROUND_HALF_UP`) to prevent IEEE-754 binary floating-point errors.

### A. Total Recognized Income
$$\text{Total Income} = \sum \text{Revenue} + \sum \text{Other Income}$$

### B. Total Recognized Expenses
$$\text{Total Expenses} = \sum \text{Operating Expense} + \sum \text{Cost of Goods Sold}$$

### C. Net Operating Surplus or Deficit
$$\text{Net Surplus} = \text{Total Income} - \text{Total Expenses}$$
*Note: This metric measures operational cash surplus and is explicitly distinguished from formal accounting profit.*

### D. Gross Profit & Margin
$$\text{Gross Profit} = \text{Revenue} - \text{Cost of Goods Sold}$$
$$\text{Gross Profit Margin (\%)} = \left(\frac{\text{Gross Profit}}{\text{Revenue}}\right) \times 100 \quad (\text{when Revenue} > 0)$$

### E. Operating Profit & Margin
$$\text{Operating Profit} = \text{Gross Profit} - \text{Operating Expenses}$$
$$\text{Operating Profit Margin (\%)} = \left(\frac{\text{Operating Profit}}{\text{Revenue}}\right) \times 100 \quad (\text{when Revenue} > 0)$$

### F. Net Profit & Margin
$$\text{Net Profit} = (\text{Revenue} + \text{Other Income}) - (\text{COGS} + \text{Operating Expenses})$$
$$\text{Net Profit Margin (\%)} = \left(\frac{\text{Net Profit}}{\text{Revenue}}\right) \times 100 \quad (\text{when Revenue} > 0)$$

### G. Cash Flow Movement
$$\text{Cash Inflows} = \sum \text{Revenue} + \sum \text{Other Income} + \sum \text{Owner Contribution}$$
$$\text{Cash Outflows} = \sum \text{Operating Expense} + \sum \text{COGS} + \sum \text{Asset Purchase} + \sum \text{Liability Payment} + \sum \text{Owner Withdrawal}$$
$$\text{Net Cash Movement} = \text{Cash Inflows} - \text{Cash Outflows}$$
$$\text{Closing Cash Balance} = \text{Opening Cash Balance} + \text{Net Cash Movement}$$
*(Internal transfers have zero net impact on total cash).*

### H. Period-over-Period Percentage Change
$$\text{Percentage Change (\%)} = \left(\frac{\text{Current Value} - \text{Previous Value}}{|\text{Previous Value}|}\right) \times 100$$
*Strict rule: Evaluated only when $|\text{Previous Value}| > 0$. If previous value is 0, the percentage change is flagged as undefined / not meaningful to prevent division by zero.*

---

## 3. Data Integrity & Safeguards

- **Zero Division Protection:** Margins and growth percentages are never divided by zero.
- **Single Currency Isolation:** Multi-currency mixing is prevented unless conversion rates are supplied. Default currency is set to `INR`.
- **CSV Formula Injection Immunity:** Prepending `'` to any cell value beginning with `=`, `+`, `-`, `@`, `\t`, `\r`.
- **Audit Logging:** Every create, edit, delete, import, and export action is timestamped and recorded in the `audit_logs` table.
