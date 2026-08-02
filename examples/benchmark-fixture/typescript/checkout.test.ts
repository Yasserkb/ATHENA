import { CheckoutService } from "./checkout";

test("CheckoutService submits an order", () => {
  expect(new CheckoutService().submit("42")).toBe("submitted:42");
});
